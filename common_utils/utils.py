import os
import random
import sys
import tempfile
from typing import Optional, List, Dict, Any

import pytorch_lightning as pl
import torch
from deepspeed.ops.adam import FusedAdam, DeepSpeedCPUAdam
from lean_dojo import Pos
from loguru import logger
from pytorch_lightning.strategies.deepspeed import DeepSpeedStrategy
from pytorch_lightning.utilities.deepspeed import (
    convert_zero_checkpoint_to_fp32_state_dict,
)
from transformers import get_constant_schedule_with_warmup

from common_utils.corpus import Corpus
from common_utils.premise import Premise


def get_all_pos_premises(annot_tac, corpus: Corpus) -> List[Premise]:
    """Return a list of all premises that are used in the tactic ``annot_tac``."""
    _, provenances = annot_tac
    all_pos_premises = set()

    for prov in provenances:
        def_path = prov["def_path"]
        p = corpus.locate_premise(def_path, Pos(*prov["def_pos"]))
        if p is not None:
            all_pos_premises.add(p)
        else:
            # logger.warning(f"Cannot locate premise: {prov}")
            pass

    return list(all_pos_premises)


def format_augmented_state(
    s: str, premises: List[Premise], max_len: Optional[int] = None, p_drop: float = 0.0
) -> str:
    """Format a state with retrieved premises and drop some of them with probability ``p_drop``."""
    aug_s = ""
    length = 0
    if max_len is None:
        max_len = 9999999999999999999999
    max_premises_len = max_len - len(bytes(s.encode("utf-8")))

    for p in premises:
        if random.random() < p_drop:
            continue
        p_str = f"{p.serialize()}\n\n"
        l = len(bytes(p_str.encode("utf-8")))
        if length + l > max_premises_len:
            continue
        length += l
        aug_s = p_str + aug_s

    aug_s += s
    return aug_s


def get_optimizers(
    parameters, trainer: pl.Trainer, lr: float, warmup_steps: int
) -> Dict[str, Any]:
    """Return an AdamW optimizer with cosine warmup learning rate schedule."""
    strategy = trainer.strategy

    if isinstance(strategy, DeepSpeedStrategy):
        if "offload_optimizer" in strategy.config["zero_optimization"]:
            logger.info("Optimizing with DeepSpeedCPUAdam")
            optimizer = DeepSpeedCPUAdam(parameters, lr=lr, adamw_mode=True)
        else:
            logger.info("Optimizing with FusedAdam")
            optimizer = FusedAdam(parameters, lr=lr, adam_w_mode=True)
    else:
        logger.info("Optimizing with AdamW")
        optimizer = torch.optim.AdamW(parameters, lr=lr)

    scheduler = get_constant_schedule_with_warmup(optimizer, warmup_steps)
    return {
        "optimizer": optimizer,
        "lr_scheduler": {
            "scheduler": scheduler,
            "interval": "step",
        },
    }


def _is_deepspeed_checkpoint(path: str):
    if not os.path.exists(path):
        raise FileExistsError(f"Checkpoint {path} does not exist.")
    return os.path.isdir(path) and os.path.exists(os.path.join(path, "zero_to_fp32.py"))


def load_checkpoint(model_cls, ckpt_path: str, device, freeze: bool):
    """Handle DeepSpeed checkpoints in model loading."""
    if _is_deepspeed_checkpoint(ckpt_path):
        with tempfile.TemporaryDirectory() as dirname:
            path = os.path.join(dirname, "lightning.cpkt")
            convert_zero_checkpoint_to_fp32_state_dict(ckpt_path, path)
            model = model_cls.load_from_checkpoint(path, strict=False).to(device)
    else:  # PyTorch Ligthning checkpoints
        model = model_cls.load_from_checkpoint(ckpt_path, strict=False).to(device)
    if freeze:
        model.freeze()
    return model


def zip_strict(*args):
    assert len(args) > 1 and all(len(args[0]) == len(a) for a in args[1:])
    return zip(*args)


def set_logger(verbose: bool) -> None:
    """
    Set the logging level of loguru.
    The effect of this function is global, and it should
    be called only once in the main function
    """
    logger.remove()
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")


def cpu_checkpointing_enabled(pl_module) -> bool:
    try:
        trainer = pl_module.trainer
        return (
            trainer.strategy is not None
            and isinstance(trainer.strategy, DeepSpeedStrategy)
            and trainer.strategy.config["activation_checkpointing"]["cpu_checkpointing"]
        )
    except RuntimeError:
        return False



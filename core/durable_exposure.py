"""Local-filesystem exposure transaction: lock + append journal + atomic head.

OS lock releases on crash. Journal is written/fsynced BEFORE head replacement.
An interrupted head update blocks prediction until explicit recovery. No stale
lock deletion, history rollback, or silent fresh retry. Not a distributed lock.
"""
from __future__ import annotations
import contextlib
import json
import os
import time
import tempfile
from pathlib import Path
from core.fault_type_final_guard import FinalTestBlocked, verify_seal, seal, guard_final_test, record_final_exposure


def atomic_json(path: Path, value: dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix=path.name+".",suffix=".partial",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as target:
            json.dump(value,target,sort_keys=True,ensure_ascii=False,allow_nan=False)
            target.flush(); os.fsync(target.fileno())
        os.replace(name,path)
        if os.name != "nt":
            directory=os.open(path.parent,os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
    finally:
        if os.path.exists(name): os.unlink(name)


@contextlib.contextmanager
def exclusive(path: Path, timeout=10.):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(str(path)+".lock",os.O_RDWR|os.O_CREAT,0o600)
    start=time.monotonic()
    try:
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    os.lseek(fd,0,os.SEEK_SET); msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic()-start >= timeout: raise FinalTestBlocked("canonical ledger is locked; no prediction")
                time.sleep(.05)
        try: yield
        finally:
            if os.name == "nt":
                os.lseek(fd,0,os.SEEK_SET); msvcrt.locking(fd,msvcrt.LK_UNLCK,1)
            else: fcntl.flock(fd,fcntl.LOCK_UN)
    finally: os.close(fd)


def _history(path): return path.with_name(path.name+".history")


def initialize(path: Path, seed: dict):
    verify_seal(seed,"ledger_checksum")
    with exclusive(path):
        if path.exists() or _history(path).exists(): raise FinalTestBlocked("canonical history already exists; refuse reset")
        _history(path).mkdir()
        atomic_json(_history(path)/"00000000.json",seed)
        atomic_json(path,seed)


def _read(path):
    entries=sorted(_history(path).glob("*.json"))
    if not path.exists() or not entries: raise FinalTestBlocked("initialize canonical ledger first")
    head=json.loads(path.read_text(encoding="utf-8")); verify_seal(head,"ledger_checksum")
    previous=None
    for sequence,entry in enumerate(entries):
        if entry.name != f"{sequence:08d}.json": raise FinalTestBlocked("canonical journal sequence missing")
        value=json.loads(entry.read_text(encoding="utf-8")); verify_seal(value,"ledger_checksum")
        if previous and value.get("previous_ledger_checksum") != previous["ledger_checksum"]: raise FinalTestBlocked("canonical history chain broken")
        previous=value
    if head["ledger_checksum"] != previous["ledger_checksum"]: raise FinalTestBlocked("head rollback/interrupted update; use recover-ledger, never fresh reset")
    return head,len(entries)


def read(path: Path):
    with exclusive(path): return _read(path)[0]


def recover(path: Path):
    """Complete an interrupted journaled head update, never delete exposure."""
    with exclusive(path):
        entries=sorted(_history(path).glob("*.json"))
        if not entries: raise FinalTestBlocked("no canonical journal")
        previous=None
        for i,entry in enumerate(entries):
            value=json.loads(entry.read_text(encoding="utf-8")); verify_seal(value,"ledger_checksum")
            if entry.name != f"{i:08d}.json" or previous and value.get("previous_ledger_checksum") != previous["ledger_checksum"]:
                raise FinalTestBlocked("history broken; manual audit required")
            previous=value
        atomic_json(path,previous)
        return previous


def register(path: Path, bundle: dict, locked: dict, *, claim: str, evaluation_id: str, expected_checksum: str):
    with exclusive(path):
        ledger,sequence=_read(path)
        if ledger["ledger_checksum"] != expected_checksum: raise FinalTestBlocked("ledger compare-and-swap changed; revalidate, no prediction")
        if any(e["evaluation_id"] == evaluation_id for e in ledger.get("evaluations",[])): raise FinalTestBlocked("evaluation ID already used; resume with receipt")
        qualification=guard_final_test(bundle,ledger,locked,claim=claim)
        updated=record_final_exposure(ledger,bundle,evaluation_id=evaluation_id)
        receipt=seal({"evaluation_id":evaluation_id,"locked_checksum":locked["locked_checksum"],
            "data_version_checksum":bundle["data_version_checksum"],"previous_ledger_checksum":ledger["ledger_checksum"],
            "claim":claim,"registered_before_prediction":True,"journal_sequence":sequence},"receipt_checksum")
        updated["evaluations"][-1]["receipt"]=receipt
        updated=seal(updated,"ledger_checksum")
        atomic_json(_history(path)/f"{sequence:08d}.json",updated)
        atomic_json(path,updated)
        return receipt,qualification


def validate_resume(path: Path, receipt: dict, bundle: dict, locked: dict, *, evaluation_id: str, claim: str):
    verify_seal(receipt,"receipt_checksum")
    ledger=read(path)
    matches=[e for e in ledger.get("evaluations",[]) if e["evaluation_id"] == evaluation_id]
    if len(matches) != 1 or matches[0].get("receipt") != receipt: raise FinalTestBlocked("resume receipt absent from canonical history")
    for key,value in (("evaluation_id",evaluation_id),("claim",claim),("locked_checksum",locked["locked_checksum"]),("data_version_checksum",bundle["data_version_checksum"])):
        if receipt[key] != value: raise FinalTestBlocked("resume binding changed")
    return {"status":"RESUME_PREVIOUSLY_EXPOSED_EVALUATION","fresh_final_test":False,"claim":claim}

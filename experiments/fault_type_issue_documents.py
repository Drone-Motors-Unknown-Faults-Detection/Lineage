"""指定 issue 的兩份可編輯文件交付，不更動封存研究產物。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from core.logger import setup_run

ROOT = Path(__file__).resolve().parents[1]
def run(pools=None, *, python, renderer):
    logger, paths = setup_run("fault_type_issue_documents")
    output = paths.output_dir
    body = (ROOT/"reports/research_closeout_20261005/final_report.md").read_text(encoding="utf-8")
    notes = (ROOT/"reports/citation_audit_20261005/content_notes.md").read_text(encoding="utf-8")
    supplement = "\n\n## 附錄三 2026年10月6日引用稽核與原待辦核對\n\n"
    supplement += "原完整報告保留，本版本加本輪勘誤與閱讀深度。不繼承舊全文聲明作本輪重新全文閱讀證據。原有所有方法數值不變。\n\n"
    supplement += (ROOT/"reports/issue_delivery_20261005/hard600_closeout.md").read_text(encoding="utf-8").replace("# ", "### ", 1)
    supplement += "\n\n"+notes.replace("# ", "### ", 1)
    research = body+supplement
    teacher = (ROOT/"reports/teacher_reply_20261005/reply.md").read_text(encoding="utf-8")
    results = []
    for name, text in [("research_report",research),("teacher_reply",teacher)]:
        source = output/(name+".md"); source.write_text(text,encoding="utf-8")
        destination = output/(name+".docx")
        code = "import json; from pathlib import Path; from reports.issue_delivery_20261005.word_format import make_word; print(json.dumps(make_word(Path("+repr(str(source))+").read_text(encoding='utf-8'), "+repr(str(destination))+"), ensure_ascii=False))"
        created = subprocess.run([str(python),"-c",code],capture_output=True,text=True,encoding="utf-8")
        if created.returncode: raise RuntimeError(created.stdout+created.stderr)
        qa = json.loads(created.stdout)
        runtime = python.parent.parent
        env = dict(os.environ, PATH=os.pathsep.join([str(runtime/"bin/override"),str(runtime/"bin/fallback"),
                   str(Path(os.environ["SystemRoot"])/"System32")]), PYTHONIOENCODING="utf-8")
        rendered = subprocess.run([str(python),str(renderer),str(destination),"--output_dir",str(output/(name+"_render")),"--verbose"],
                                  capture_output=True,text=True,encoding="utf-8",env=env)
        log = output/(name+"_render.log"); log.write_text(rendered.stdout+rendered.stderr,encoding="utf-8")
        qa.update(renderer_exit_code=rendered.returncode, render_log=str(log), desktop_libreoffice_used=False,
                  layout_status="RENDERED_PENDING_VISUAL_REVIEW" if rendered.returncode == 0 else "LAYOUT_UNVERIFIED",
                  markdown_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        results.append(qa)
        logger.info("{}：結構{}；版面{}",name,qa["structural_status"],qa["layout_status"])
    (output/"document_qa.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    return dict(output=str(output),documents=results,trained_models=0,new_predictions=0)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python",type=Path,required=True)
    parser.add_argument("--renderer",type=Path,required=True)
    print(json.dumps(run(**vars(parser.parse_args(argv))),ensure_ascii=False))
if __name__ == "__main__": main()

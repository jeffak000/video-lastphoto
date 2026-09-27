#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频尾帧提取器（高清）
- 提取视频最后一帧（或结尾前 N 秒的帧），原分辨率无损输出
- 支持单文件 / 批量文件夹
- 依赖系统 ffmpeg / ffprobe（本机已装 WinGet 版）
用法：
  图形界面： python3 video_tailframe.py
  命令行：   python3 video_tailframe.py --cli 视频.mp4 --out 输出目录
  批量：     python3 video_tailframe.py --batch 视频文件夹 --out 输出目录
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


# ---------- 定位 ffmpeg / ffprobe ----------
def locate(tool):
    p = shutil.which(tool)
    if p:
        return p
    # Windows 常见安装位置兜底
    if sys.platform.startswith("win"):
        home = os.path.expanduser("~")
        cands = [
            os.path.join(home, "AppData", "Local", "Microsoft", "WinGet", "Links", tool + ".exe"),
            r"C:\ffmpeg\bin" + tool + ".exe",
        ]
        for c in cands:
            if os.path.isfile(c):
                return c
    return None


FFMPEG = locate("ffmpeg")
FFPROBE = locate("ffprobe")


# ---------- 视频信息 ----------
def get_info(path):
    """返回 (时长秒, 宽, 高) 或 None"""
    if not FFPROBE:
        return None
    try:
        dur = subprocess.check_output(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        wh = subprocess.check_output(
            [FFPROBE, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height",
             "-of", "csv=s=x:p=0", path],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        duration = float(dur) if dur else 0.0
        if "x" in wh:
            w, h = wh.split("x")
            return duration, int(w), int(h)
        return duration, None, None
    except Exception:
        return None


# ---------- 提取核心 ----------
def extract_tail(input_path, out_path, offset=0.1, precise=False,
                 quality=2, duration=None):
    """
    input_path: 源视频
    out_path:    输出图片（扩展名决定格式 png/jpg）
    offset:      快速模式从结尾往前多少秒取帧
    precise:     精确模式（逐帧解码到接近结尾，慢但取到真正尾帧）
    quality:     -q:v 值（PNG 无损；JPG 越小越清晰）
    duration:    ffprobe 得到的时长，用于精确模式
    返回: (成功 bool, 信息 str)
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if precise and duration:
        t = max(0.0, duration - 0.04)
        cmd = [FFMPEG, "-i", input_path, "-ss", f"{t:.3f}",
               "-frames:v", "1", "-q:v", str(quality), str(out_path), "-y"]
    else:
        cmd = [FFMPEG, "-sseof", f"-{offset}", "-i", input_path,
               "-frames:v", "1", "-q:v", str(quality), str(out_path), "-y"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return False, res.stderr.strip().splitlines()[-1] if res.stderr.strip() else "未知错误"
        if out_path.exists() and out_path.stat().st_size > 0:
            return True, str(out_path)
        return False, "未生成图片"
    except Exception as e:
        return False, str(e)


def process_one(input_path, out_dir, fmt, offset, precise, quality):
    info = get_info(input_path)
    duration = info[0] if info else None
    stem = Path(input_path).stem
    out_path = Path(out_dir) / f"{stem}_尾帧.{fmt}"
    ok, msg = extract_tail(input_path, out_path, offset, precise, quality, duration)
    return ok, msg, out_path, info


# ---------- 命令行模式 ----------
def run_cli(args):
    if not FFMPEG or not FFPROBE:
        print("错误：未找到 ffmpeg / ffprobe，请先安装并加入 PATH。")
        sys.exit(1)
    files = []
    if args.cli:
        files = [args.cli]
    elif args.batch:
        exts = (".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm", ".m4v", ".ts", ".wmv")
        files = [str(p) for p in sorted(Path(args.batch).rglob("*"))
                 if p.suffix.lower() in exts]
    out_dir = args.out or (os.path.dirname(args.cli) if args.cli else args.batch)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    print(f"共 {len(files)} 个视频，输出目录：{out_dir}\n")
    for f in files:
        ok, msg, out_path, info = process_one(
            f, out_dir, args.format, args.offset, args.precise,
            2 if args.format == "png" else 2)
        if ok:
            size = ""
            if info and info[1]:
                size = f"  分辨率 {info[1]}x{info[2]}"
            print(f"[OK]  {Path(f).name} -> {out_path}{size}")
        else:
            print(f"[失败] {Path(f).name}: {msg}")


# ---------- 图形界面 ----------
def run_gui():
    if not FFMPEG or not FFPROBE:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        from tkinter import messagebox
        messagebox.showerror("缺少依赖",
            "未检测到 ffmpeg / ffprobe。\n请先安装 FFmpeg 并加入系统 PATH，再运行本工具。")
        sys.exit(1)

    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("视频尾帧提取器 · 高清")
    root.geometry("640x520")
    root.resizable(False, False)

    # 变量
    src_var = tk.StringVar()
    out_var = tk.StringVar()
    fmt_var = tk.StringVar(value="png")
    offset_var = tk.DoubleVar(value=0.1)
    precise_var = tk.BooleanVar(value=False)
    info_var = tk.StringVar(value="未选择视频")
    log_lines = []

    def log(msg):
        log_lines.append(msg)
        log_box.insert("end", msg + "\n")
        log_box.see("end")
        root.update_idletasks()

    def pick_file():
        p = filedialog.askopenfilename(
            title="选择视频",
            filetypes=[("视频", "*.mp4 *.mov *.mkv *.avi *.flv *.webm *.m4v *.ts *.wmv"), ("全部", "*.*")])
        if p:
            src_var.set(p)
            refresh_info()

    def pick_dir():
        p = filedialog.askdirectory(title="选择输出目录")
        if p:
            out_var.set(p)

    def refresh_info():
        p = src_var.get()
        if not p or not os.path.isfile(p):
            info_var.set("未选择视频")
            return
        info = get_info(p)
        if not info:
            info_var.set("无法读取信息（可能非视频文件）")
            return
        dur, w, h = info
        sz = f"{w}x{h}" if w else "未知"
        info_var.set(f"时长 {dur:.2f}s ｜ 分辨率 {sz} ｜ 输出将保持原分辨率高清")

    def do_extract():
        src = src_var.get()
        if not src or not os.path.isfile(src):
            messagebox.showwarning("提示", "请先选择视频文件。")
            return
        fmt = fmt_var.get()
        offset = offset_var.get()
        precise = precise_var.get()
        out_dir = out_var.get() or os.path.dirname(src)
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        info = get_info(src)
        duration = info[0] if info else None
        stem = Path(src).stem
        out_path = Path(out_dir) / f"{stem}_尾帧.{fmt}"
        log(f"提取中：{Path(src).name} ...")
        ok, msg, _, _ = extract_tail(src, out_path, offset, precise,
                                     2 if fmt == "png" else 2, duration)
        if ok:
            log(f"✅ 完成：{out_path}")
            try:
                os.startfile(str(out_path.parent))
            except Exception:
                pass
        else:
            log(f"❌ 失败：{msg}")

    def do_batch():
        d = filedialog.askdirectory(title="选择含视频的文件夹（将递归处理）")
        if not d:
            return
        fmt = fmt_var.get()
        offset = offset_var.get()
        precise = precise_var.get()
        out_dir = out_var.get() or d
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        exts = (".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm", ".m4v", ".ts", ".wmv")
        files = [str(p) for p in sorted(Path(d).rglob("*")) if p.suffix.lower() in exts]
        if not files:
            messagebox.showinfo("提示", "该文件夹下未找到视频文件。")
            return
        log(f"批量模式：找到 {len(files)} 个视频")
        for f in files:
            ok, msg, out_path, info = process_one(f, out_dir, fmt, offset, precise,
                                                  2 if fmt == "png" else 2)
            if ok:
                log(f"✅ {Path(f).name} -> {out_path}")
            else:
                log(f"❌ {Path(f).name}: {msg}")
        log("批量完成。")
        try:
            os.startfile(out_dir)
        except Exception:
            pass

    # ---- 布局 ----
    tk.Label(root, text="视频尾帧提取器（高清原分辨率输出）",
             font=("Microsoft YaHei", 14, "bold")).pack(pady=10)

    frm = tk.Frame(root)
    frm.pack(fill="x", padx=20)
    tk.Entry(frm, textvariable=src_var, width=52).pack(side="left", fill="x", expand=True)
    tk.Button(frm, text="选择视频", command=pick_file).pack(side="left", padx=5)

    tk.Label(root, textvariable=info_var, fg="gray", wraplength=580,
             justify="left").pack(anchor="w", padx=22, pady=4)

    # 选项区
    opt = tk.LabelFrame(root, text="输出选项", padx=10, pady=8)
    opt.pack(fill="x", padx=20, pady=4)

    row1 = tk.Frame(opt); row1.pack(fill="x", pady=2)
    tk.Label(row1, text="格式：").pack(side="left")
    tk.Radiobutton(row1, text="PNG 无损高清", variable=fmt_var, value="png").pack(side="left")
    tk.Radiobutton(row1, text="JPG 高质量", variable=fmt_var, value="jpg").pack(side="left", padx=10)
    tk.Checkbutton(row1, text="精确取真正尾帧（较慢）", variable=precise_var).pack(side="left")

    row2 = tk.Frame(opt); row2.pack(fill="x", pady=2)
    tk.Label(row2, text="快速模式取结尾前(秒)：").pack(side="left")
    tk.Spinbox(row2, from_=0.05, to=5.0, increment=0.05, width=8,
               textvariable=offset_var).pack(side="left")
    tk.Label(row2, text="（0.05~5，越小越接近尾帧）").pack(side="left", padx=6)

    row3 = tk.Frame(opt); row3.pack(fill="x", pady=2)
    tk.Entry(row3, textvariable=out_var, width=46).pack(side="left", fill="x", expand=True)
    tk.Button(row3, text="输出目录", command=pick_dir).pack(side="left", padx=5)

    # 按钮区
    btn = tk.Frame(root); btn.pack(pady=10)
    tk.Button(btn, text="提取尾帧高清图", width=18, height=2,
              bg="#2e7d32", fg="white", command=do_extract).pack(side="left", padx=6)
    tk.Button(btn, text="批量文件夹", width=14, height=2,
              command=do_batch).pack(side="left", padx=6)

    # 日志
    tk.Label(root, text="日志", anchor="w").pack(anchor="w", padx=22)
    log_box = tk.Text(root, height=9)
    log_box.pack(fill="both", padx=20, pady=4)

    root.mainloop()


def _popup(title, text, has_gui):
    if has_gui:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(title, text)
            return
        except Exception as e:
            print(f"[弹窗不可用，改用控制台] {title}: {text} ({e})")
    print(f"[{title}] {text}")


def run_shell(path):
    """右键菜单直接提取：取尾帧高清图到同目录，弹窗反馈。"""
    try:
        import tkinter as tk  # noqa
        from tkinter import messagebox  # noqa
        has_gui = True
    except Exception:
        has_gui = False
    if not os.path.isfile(path):
        _popup("错误", f"文件不存在：{path}", has_gui)
        return
    info = get_info(path)
    duration = info[0] if info else None
    out = Path(path).parent / f"{Path(path).stem}_尾帧.png"
    ok, msgtxt = extract_tail(path, out, 0.1, False, 2, duration)
    if ok:
        _popup("完成", f"尾帧已保存：\n{out}", has_gui)
        try:
            os.startfile(str(out.parent))
        except Exception:
            pass
    else:
        _popup("失败", msgtxt, has_gui)


def main():
    parser = argparse.ArgumentParser(description="视频尾帧提取器（高清）")
    parser.add_argument("--cli", metavar="VIDEO", help="单文件命令行提取")
    parser.add_argument("--batch", metavar="DIR", help="批量处理文件夹（递归）")
    parser.add_argument("--out", help="输出目录（默认源同目录）")
    parser.add_argument("--offset", type=float, default=0.1, help="快速模式结尾前秒数")
    parser.add_argument("--precise", action="store_true", help="精确取真正尾帧")
    parser.add_argument("--format", choices=["png", "jpg"], default="png")
    parser.add_argument("--shell", metavar="FILE",
                        help="右键菜单直接提取该视频的尾帧高清图")
    args = parser.parse_args()

    if args.cli or args.batch:
        run_cli(args)
    elif args.shell:
        run_shell(args.shell)
    else:
        run_gui()


if __name__ == "__main__":
    main()

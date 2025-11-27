import os
import sublime
import sublime_plugin


INCLUDE_DIR  =  'include'
SOURCE_DIR  =  'source'
HEADER_EXTS  =  ['.hpp', '.h']
SOURCE_EXTS  =  ['.cpp', '.c']
CASE_SENSITIVE  =  True


AUTO_OPENED  =  set()


def normalize(s):
    return s  if  CASE_SENSITIVE  else  s.lower()


def find_root_dir(path):
    parts  =  path.split(os.sep)

    for  i, part  in  enumerate(parts):
        if  (normalize(part))  in  (normalize(INCLUDE_DIR), normalize(SOURCE_DIR)):
            return os.sep.join(parts[:i])

    return None


def find_paired_file(path):
    root  =  find_root_dir(path)

    if  not  root:
        return None

    parts  =  path.split(os.sep)

    if  (normalize(INCLUDE_DIR))  in  (
      parts  if  CASE_SENSITIVE  else  [p.lower()  for  p  in  parts]
    ):
        base_dir  =  INCLUDE_DIR
        target_dir  =  SOURCE_DIR
        exts  =  SOURCE_EXTS

    else:
        base_dir  =  SOURCE_DIR
        target_dir  =  INCLUDE_DIR
        exts  =  HEADER_EXTS

    idx  =  [
        i  for  i, p  in  enumerate(parts)  if (
            p  ==  base_dir  if  CASE_SENSITIVE  else  p.lower()  ==  base_dir.lower()
        )][0]

    sub_path  =  os.sep.join(parts[idx  +  1:])

    name, _  =  os.path.splitext(sub_path)

    target_path_base  =  os.path.join(root, target_dir, name)

    for  ext  in  exts:
        candidate  =  target_path_base  +  ext

        if  os.path.isfile(candidate):
            return candidate

    return None


def open_file(window, path):
    if  not  path  or  not  os.path.isfile(path):
        return

    if  normalize(path)  in  AUTO_OPENED:
        return

    AUTO_OPENED.add(normalize(path))
    window.open_file(path, sublime.ENCODED_POSITION)


class PairedFileListener(sublime_plugin.EventListener):
    def on_load_async(self, view):
        path  =  view.file_name()

        if  not  path:
            return

        if  normalize(path)  in  AUTO_OPENED:
            AUTO_OPENED.discard(normalize(path))
            return

        paired  =  find_paired_file(path)

        if  paired:
            open_file(view.window(), paired)

import sublime
import sublime_plugin
import os
import re


def parse_class_name(text):
    # pega o primeiro "class Nome"
    m = re.search(r'\bclass\s+(\w+)', text)
    return m.group(1) if m else None


def extract_public_block(text):
    # tenta pegar só o bloco public: ... até próximo private/protected/};
    m = re.search(r'public:\s*(.*?)(?:private:|protected:|};)', text,
                  re.DOTALL)
    if not m:
        return ""
    block = m.group(1)
    # tira comentários
    block = re.sub(r'//.*', '', block)
    block = re.sub(r'/\*.*?\*/', '', block, flags=re.DOTALL)
    return block


def parse_methods(class_name, text):
    block = extract_public_block(text)
    lines = re.findall(r'(.*?);', block)
    methods = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if '(' not in line:      # provavelmente campo, não função
            continue

        # ignora =default, =delete inline, deixa só assinatura crua
        line = re.sub(r'\s*=\s*default', '', line)
        line = re.sub(r'\s*=\s*delete', '', line)

        methods.append(line)

    return methods


def build_method_definition(class_name, decl):
    # decl vem sem ; no final
    original = decl.strip()

    # nome + parênteses + sufixo (const, noexcept, override, etc.)
    m = re.match(
        r'(?P<prefix>.*?)\b(?P<name>~?%s|operator[^\s(]+|\w+)\s*'
        r'(?P<params>\(.*\))\s*(?P<suffix>.*)$' % class_name,
        original
    )

    if not m:
        return f"// TODO: não consegui gerar para: {original}\n"

    prefix = m.group('prefix').strip()
    name = m.group('name').strip()
    params = m.group('params').strip()
    suffix = m.group('suffix').strip()

    # monta assinatura completa
    if name == class_name:
        # construtor
        signature = f"{class_name}::{class_name}{params}"
        if suffix:
            signature += " " + suffix
    elif name == f"~{class_name}":
        # destrutor
        signature = f"{class_name}::~{class_name}{params}"
        if suffix:
            signature += " " + suffix
    else:
        # método normal / operator
        return_type = prefix if prefix else "/*RETORNO*/"
        signature = f"{return_type} {class_name}::{name}{params}"
        if suffix:
            signature += " " + suffix

    body_lines = []

    if name.startswith("operator="):
        body_lines.append("    if (this == &other)")
        body_lines.append("        return *this;")
        body_lines.append("")
        body_lines.append("    // TODO: copiar/mover campos")
        body_lines.append("")
        body_lines.append("    return *this;")
    elif name == class_name or name == f"~{class_name}":
        # construtor / destrutor vazio
        pass
    else:
        body_lines.append("    // TODO: implementar")

    body = "\n".join(body_lines)
    return f"{signature}\n{{\n{body}\n}}\n"


def generate_cpp_from_hpp(hpp_path, text):
    base = os.path.basename(hpp_path)
    class_name = parse_class_name(text)
    if not class_name:
        return None, "// Não achei declaração de classe.\n"

    methods = parse_methods(class_name, text)

    cpp_lines = [f'#include "{base}"', ""]
    for decl in methods:
        decl = decl.rstrip(';').strip()
        cpp_lines.append(build_method_definition(class_name, decl))
        cpp_lines.append("")

    return os.path.splitext(base)[0] + ".cpp", "\n".join(cpp_lines)


class GenerateCppFromHppCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if not view:
            return

        hpp_path = view.file_name()
        if not hpp_path or not hpp_path.endswith(".hpp"):
            sublime.error_message("Abre um .hpp primeiro, mano.")
            return

        text = view.substr(sublime.Region(0, view.size()))
        cpp_name, cpp_content = generate_cpp_from_hpp(hpp_path, text)

        # cria nova aba com nome sugerido .cpp
        new_view = self.window.new_file()
        new_view.set_name(cpp_name)
        new_view.set_syntax_file("Packages/C++/C++.sublime-syntax")

        # ajuda o diálogo de salvar a ir pro mesmo diretório
        dir_name = os.path.dirname(hpp_path)
        new_view.settings().set("default_dir", dir_name)

        new_view.run_command("append", {"characters": cpp_content})
        new_view.set_scratch(False)

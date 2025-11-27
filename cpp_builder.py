import os
import re
import subprocess
import sys
import time


DEBUG_MODE = True
COMPILER = 'g++'
CPP_VERSION = 'c++23'
INCLUDE_DIR = 'include'
SOURCE_DIR = 'source'
OUTPUT_DIR = 'build'
OUTPUT_EXT = '.out'
SUPPORTED_EXTS = ['.c', '.cpp', '.h', '.hpp']


def validate_args():
    if len(sys.argv) < 2:
        print('[ERROR]: Insufficient arguments.')
        sys.exit(1)

    ext = os.path.splitext(sys.argv[1])[1]

    if ext not in SUPPORTED_EXTS:
        print(f'[ERROR]: Unsupported file extension: {ext}')
        sys.exit(1)


def get_library_flags(libraries):
    library_flags = ''

    if 'raylib' in libraries:
        library_flags += '-lraylib -lGL -lm -lpthread -ldl -lrt -lX11'

    library_flags = library_flags.split(' ') if library_flags else []

    return library_flags


def find_source_dir(file_path):
    full_path = os.path.abspath(file_path)
    parts = full_path.split(os.sep)

    for i in range(len(parts), 0, -1):
        if parts[i - 1] == SOURCE_DIR:
            return os.sep.join(parts[:i])
        elif parts[i - 1] == INCLUDE_DIR:
            return os.path.join(os.sep.join(parts[:i - 1]), SOURCE_DIR)

    return None


def find_source_files(source_dir):
    source_files = []

    if not source_dir:
        print(f'[ERROR]: directory {SOURCE_DIR} not found.')
        sys.exit(1)

    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith(('.c', '.cpp')):
                source_files.append(os.path.join(root, file))

    return source_files


def validate_source_files(source_files):
    if not source_files:
        print('[ERROR]: source files not found.')
        sys.exit(1)


def to_snake_case(text):
    snake_text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
    snake_text = re.sub(r'[-\s]', '_', snake_text)
    snake_text = snake_text.lower()

    return snake_text


def build(build_command, project_dir):
    result = subprocess.run(build_command, cwd=project_dir, capture_output=True, text=True)

    return result


def run(result, output, output_dir):
    if result.returncode == 0:
        print(f'[INFO]: Running program in: {output}')
        subprocess.run([f'./{os.path.basename(output)}'], cwd=output_dir)
    else:
        print('[ERROR]: Compilation failed.')
        print('Compiler error:')
        print(result.stderr)


def main():
    start = time.time()
    validate_args()

    file_path = sys.argv[1]
    libraries = sys.argv[2] if len(sys.argv) > 2 else ''

    library_flags = get_library_flags(libraries)
    source_dir = find_source_dir(file_path)
    source_files = find_source_files(source_dir)

    validate_source_files(source_files)

    project_dir = os.path.abspath(os.path.join(source_dir, '..'))
    include_dir = os.path.join(project_dir, INCLUDE_DIR)
    output_dir = os.path.join(project_dir, OUTPUT_DIR)

    project_name = os.path.basename(project_dir)
    project_name = to_snake_case(project_name)
    output = os.path.join(output_dir, f'{project_name}{OUTPUT_EXT}')

    os.makedirs(output_dir, exist_ok=True)

    build_command = [
        COMPILER,
        f'-std={CPP_VERSION}',
        *(['-g'] if DEBUG_MODE else ['-O2']),
        '-o',
        output,
        *source_files,
        '-I',
        include_dir,
        *library_flags
    ]

    build_command_str = ' '.join(build_command)

    print(f'[INFO]: Build Command: {build_command_str}')

    result = build(build_command, project_dir)

    end = time.time()
    elapsed = end - start
    print(f'[INFO]: Elapsed time: {elapsed:.2f} seconds.')

    run(result, output, output_dir)


if __name__ == '__main__':
    main()

from compression import zstd
import pickle


def write_project(project, compression_level=10):
    with zstd.open(project.path, "wb", level=compression_level) as f:
        pickle.dump(project, f)


def read_project(project_path):
    with zstd.open(project_path, "rb") as f:
        project = pickle.load(f)

    # Update path if file name/path changed
    project.path = project_path

    return project
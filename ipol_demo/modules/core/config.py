import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    # core
    server_environment: str = os.environ.get("env", "local")
    logs_dir: str = "logs/"
    config_common_dir: str = (
        os.path.expanduser("~") + "/ipolDevel/ipol_demo/modules/config_common"
    )
    authorized_patterns: str = f"{config_common_dir}/authorized_patterns.conf"

    base_url: str = os.environ["IPOL_URL"]

    project_folder = os.path.expanduser("~") + "/ipolDevel"

    shared_folder_rel: str = "shared_folder/"
    shared_folder_abs = os.path.join(project_folder, shared_folder_rel)
    # demo_extras_main_dir = os.path.join(shared_folder_abs, "demoExtras/")
    # dl_extras_dir = os.path.join(shared_folder_abs, "dl_extras/")
    share_run_dir_rel: str = "run/"
    share_run_dir_abs = os.path.join(shared_folder_abs, share_run_dir_rel)

    # demoinfo
    demoinfo_db: str = "db/demoinfo.db"
    demoinfo_dl_extras_dir: str = "staticData/demoExtras"

    # dispatcher
    demorunners_path = (
        os.path.expanduser("~")
        + "/ipolDevel/ipol_demo/modules/config_common/demorunners.xml"
    )
    policy: str = "lowest_workload"

    # archive
    archive_blobs_dir: str = "staticData/archive_blobs/"
    archive_thumbs_dir: str = "staticData/archive_thumbs/"
    database_dir: str = "db"
    database_file: str = "db/archive.db"
    number_of_experiments_by_pages: int = 5

    # Blobs
    blobs_database_file: str = "db/blobs.db"
    blobs_data_root: str = os.path.expanduser("~") + "/ipolDevel/ipol_demo/modules/core"

    blob_dir: str = "staticData/blobs/blob_directory"
    thumb_dir: str = "staticData/blobs/thumbnail"
    vr_dir: str = "staticData/blobs/visrep"


settings = Settings()

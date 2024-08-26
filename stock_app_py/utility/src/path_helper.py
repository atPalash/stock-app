from pathlib import Path
from stock_app_py.utility.src.yaml_parser import read_config


def get_app_path(config_id: str) -> str:
    try:
        path = mapped_config[config_id](config_id)
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist")
        return str(mapped_config[config_id](config_id).resolve())
    except Exception as e:
        raise


def __file_path(config_id: str) -> Path:
    id, ftype = config_id.split(".")
    path = helper_file_path.parent.parent.parent.parent / f"configuration/{id}.{ftype}"
    return path


def __dir_path(config_id: str) -> Path:
    path = helper_file_path.parent.parent.parent.parent / f"{config_id}"
    return path


def __dir_path_html(config_id: str) -> Path:
    path = helper_file_path.parent.parent.parent.parent / f"stock_app_html/{config_id}"
    return path


mapped_config = {
    "config.yaml": __file_path,
    "index_stock.yaml": __file_path,
    "indicator.yaml": __file_path,
    "selected_stocks.yaml": __file_path,
    "user_config.json": __file_path,
    "users_config.json": __file_path,
    "rs_rating.csv": __file_path,
    "configuration": __dir_path,
    "database": __dir_path,
    "static": __dir_path_html,
    "templates": __dir_path_html,
    "EQUITY_L.csv": __file_path,
    "test_indicator.yaml": __file_path,
    "CF-Event-equities.csv": __file_path,
}
helper_file_path = Path(__file__)

if __name__ == "__main__":
    print(get_app_path("configuration"))

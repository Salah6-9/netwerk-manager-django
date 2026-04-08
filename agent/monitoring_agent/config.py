import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("agent.config")

CONFIG_FILE = "config.json"

_cached_json_config = None

def _load_json():
    global _cached_json_config
    if _cached_json_config is not None:
        return _cached_json_config
        
    if not os.path.exists(CONFIG_FILE):
        _cached_json_config = {}
        return _cached_json_config

    try:
        with open(CONFIG_FILE) as f:
            _cached_json_config = json.load(f)
    except (json.JSONDecodeError, IOError):
        _cached_json_config = {}
        
    return _cached_json_config

def get_config(key, default=None):
    """
    Tiered fallback:
    1. Environment Variable (prefixed with AGENT_)
    2. config.json
    3. Default value
    """
    env_key = f"AGENT_{key.upper()}"
    
    # 1. Try Environment Variable
    env_val = os.getenv(env_key)
    if env_val is not None:
        logger.info(f"Loaded {key} from environment variable {env_key}")
        # Cast to int if default is int
        if isinstance(default, int) and not isinstance(env_val, int):
            try: return int(env_val)
            except ValueError: pass
        return env_val

    # 2. Try JSON file
    json_config = _load_json()
    if key in json_config:
        logger.info(f"Loaded {key} from {CONFIG_FILE}")
        return json_config[key]

    # 3. Fallback to default
    if default is not None:
        logger.info(f"Using default value for {key}")
    return default

def save_config(data):
    """Save configuration back to JSON file"""
    global _cached_json_config
    # Merge existing config with new data if necessary, or just overwrite
    _cached_json_config = data
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)
    logger.info(f"Configuration saved to {CONFIG_FILE}")

def update_config_key(key, value):
    """Update a single key in the JSON configuration"""
    config = _load_json()
    config[key] = value
    save_config(config)

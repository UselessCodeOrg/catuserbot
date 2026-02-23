import logging
import os
import pwd
from pathlib import Path
import subprocess

# Logger = = = = =
logger = logging.getLogger("Service Setup")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Constants = = = = =
UV_BIN_DIR = Path.home() / ".local" / "bin"
SUBPROCESS_ENV = {**os.environ, "PATH": f"{UV_BIN_DIR}:{os.environ.get('PATH', '')}"}

COMMANDS_STAGE_1 = [
    "curl -LsSf https://astral.sh/uv/install.sh | sh",
    "UV_PYTHON_INSTALL_DIR=/opt/uv-python uv venv --python 3.11",
    "uv pip install -r requirements.txt",
    "apt-get install -y postgresql postgresql-contrib",
]

COMMANDS_STAGE_3 = [
    "systemctl enable catuserbot.service",
    "systemctl start catuserbot.service",
    "systemctl status catuserbot.service",

]


# Helper functions = = = = =
def setup_database(db_name="catuserbot", user="postgres", password="pswd"):
    """Create the database"""
    try:
        subprocess.run(
            f'''sudo -u postgres psql -c "ALTER USER {user} WITH PASSWORD \'{password}\';" ''',
            shell=True,
            check=True,
        )

        # Check if DB already exists
        result = subprocess.run(
            f'''sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname=\'{db_name}\'" ''',
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
        db_exists = result.stdout.strip() == "1"

        if db_exists:
            print(f"\nDatabase \'{db_name}\' already exists.")
            print("  [1] Keep existing database and continue")
            print("  [2] Drop and recreate (ALL DATA WILL BE LOST)")
            choice = input("Enter choice (1/2): ").strip()

            if choice == "2":
                confirm = input(f"Are you sure you want to delete \'{db_name}\'? Type YES to confirm: ").strip()
                if confirm == "YES":
                    subprocess.run(
                        f"sudo -u postgres dropdb {db_name}",
                        shell=True,
                        check=True,
                    )
                    logger.info("Dropped existing database '%s'.", db_name)
                else:
                    logger.info("Drop cancelled. Continuing with existing database.")
                    return
            else:
                logger.info("Keeping existing database '%s'.", db_name)
                return

        subprocess.run(
            f"sudo -u postgres createdb {db_name} -O {user}",
            shell=True,
            check=True,
        )
        logger.info("Database '%s' created.", db_name)

    except subprocess.CalledProcessError as e:
        logger.error("Database setup failed: %s", e, exc_info=True)
        raise


def is_database_operational(db_name="catuserbot", user="postgres"):
    try:
        subprocess.run(
            ["psql", "-U", user, "-d", db_name, "-c", "SELECT 1;"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(e, exc_info=True)
        return False
    except Exception as e:
        logger.error(e, exc_info=True)
        return False





# Stages = = = = =
def stage_1():
    """Installing the necessary things"""
    for cmd in COMMANDS_STAGE_1:
        logger.info("Running: %s", cmd)
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                env=SUBPROCESS_ENV,  # ensures uv binary is findable after install
            )
            if result.stdout:
                logger.info(result.stdout)
            if result.stderr:
                logger.warning(result.stderr)
        except subprocess.CalledProcessError as e:
            logger.error("Command failed: %s\n%s", cmd, e.stderr, exc_info=True)
            raise

    setup_database()


def stage_2(catuserbot_path: Path):
    """Config var check"""
    venv_python = catuserbot_path / ".venv" / "bin" / "python3"
    checker_script = catuserbot_path / "_install_checker.py"
    result = subprocess.run(
        [str(venv_python), str(checker_script)],
        text=True,
        cwd=str(catuserbot_path),
    )
    if result.returncode != 0:
        raise RuntimeError("Stage 2 checks failed — see errors above.")
    logger.info("All stage 2 checks passed.")


def stage_3():
    """Converting into service"""
    user = os.environ.get("SUDO_USER") or pwd.getpwuid(os.getuid()).pw_name

    current_file = Path(__file__)
    catuserbot_path = current_file.parent
    userbot_path = catuserbot_path / "userbot"
    venv_python_path = catuserbot_path / ".venv" / "bin" / "python3"
    catuserbot_bin_path = catuserbot_path / "bin"
    service_file = f"""
[Unit]
Description="A simple Telegram userbot based on Telethon "
Requires=network.target
After=network.target

[Service]
User={user}
Type=simple
ExecStart={venv_python_path} -m userbot
WorkingDirectory={catuserbot_path}
Restart=always

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    file = open("/etc/systemd/system/catuserbot.service","w")
    file.write(service_file)
    file.close()

    subprocess.run(
        f"chown -R {user}:{user} {str(catuserbot_path/".venv")}",
        shell = True,
        check = True,
        text = True
        )

    for cmd in COMMANDS_STAGE_3:
        logger.info("Running: %s", cmd)
        try:
            subprocess.run(
                cmd,
                check=True,
                text=True,
                shell=True
            )
        except subprocess.CalledProcessError as e:
            logger.error("Command failed: %s\n%s", cmd, e.stderr, exc_info=True)
            raise


# Main function
def main():
    catuserbot_path = Path(__file__).parent
    stage_1()
    stage_2(catuserbot_path)
    stage_3()


# Entry point
if __name__ == "__main__":
    if os.getegid() != 0:
        print("Uses sudo to run this script, this script makes a new process thats why sudo permission is essential. Check install_as_service.py and _install_checker.py is you are concerned about security. Thank you!")
    main()
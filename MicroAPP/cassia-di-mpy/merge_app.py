import sys
import json

if len(sys.argv) < 2:
    print("no $MERGE_PY argument")
    exit


MERGE_PY = sys.argv[1]

FILES = [
    "./src/microdot.py",
    "./src/cassia_log.py",
    "./src/cassia_time.py",
    "./src/error.py",
    "./src/meta.py",
    "./src/cassia_uuid.py",
    "./src/waiter_manager.py",
    "./src/mqtt_as.py",
    "./src/mqtt.py",
    "./src/cassiablue_manager.py",
    "./src/profile_model.py",
    "./src/profile_manager.py",
    "./src/task_entry.py",
    "./src/task_manager.py",
    "./src/cassia_device.py",
    "./src/bypass.py",
    "./src/http_server.py",
    "./src/main.py",
]


def main():
    print(MERGE_PY)

    includes = [x.split("/")[-1].rsplit(".", 1)[0] for x in FILES]
    print("\ninclude files:", json.dumps(includes))

    with open(MERGE_PY, "w") as dst:
        dst.write(f"# {MERGE_PY}\n")

        for filepath in FILES:
            with open(filepath, "r") as src:
                dst.write("\n\n")
                dst.write("#=============================\n")
                dst.write(f"# {filepath}\n")
                dst.write("#=============================\n")

                for line in src:
                    if line.startswith("from "):
                        module_name = line.split(" ")[1]
                        if module_name in includes:
                            dst.write(f"#{line}")
                        else:
                            dst.write(line)
                    else:
                        dst.write(line)

                dst.write("\n")


if __name__ == "__main__":
    main()

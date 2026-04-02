import json
import sys
from enum import IntEnum


import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

from logger import logger


class Stage(IntEnum):
    WAIT_IN_QUEUE = 0
    CONNECT = 1
    GET_LOGS = 2


COLOR_MAP = {
    "[High->Low] ALL": "rgb(127, 219, 255)",
    "[High->Medium] wait_in_queue": "rgba(255, 220, 0, 0.8)",
    "[High->Medium] retry": "rgb(255, 88, 34)",
    "[High->Medium] connect": "rgb(1, 255, 112)",
    "[High->Medium] get_logs": "rgb(27, 123, 255)",
    "[Medium->Low] wait_in_queue": "rgba(255, 220, 0, 0.8)",
    "[Medium->Low] retry": "rgb(255, 88, 34)",
    "[Medium->Low] connect": "rgb(1, 255, 112)",
    "[Medium->Low] get_logs": "rgb(27, 123, 255)",
}


def render_info_table(json_data, history_file):
    worker_num = json_data["worker_num"]
    all_start = json_data["history"][0]["start_ts"]
    all_end = json_data["history"][0]["end_ts"]
    devices = json_data["history"][0]["devices"]

    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=["Devices History Info", "Gateway Chip Statistics"],
        specs=[[{"type": "domain"}], [{"type": "domain"}]],
    )

    tasks_count = 0
    for _, v in devices.items():
        if "3 -> 2" in v:
            tasks_count = tasks_count + 1
        if "2 -> 1" in v:
            tasks_count = tasks_count + 1

    info_table_header = [
        "worker_num",
        "all_start",
        "all_end",
        "devices",
        "tasks",
        "cost(s)",
        "average(s)",
    ]

    info_table_cells = [
        worker_num,
        all_start,
        all_end,
        len(devices),
        tasks_count,
        all_end - all_start,
        (all_end - all_start) / tasks_count,
    ]

    fig.add_trace(
        go.Table(
            header=dict(
                values=info_table_header, fill_color="paleturquoise", align="left"
            ),
            cells=dict(values=info_table_cells, fill_color="lavender", align="left"),
        ),
        row=1,
        col=1,
    )

    chip_table_header = [
        "chip_id",
        "tasks_count",
        "conn_cost_max(s)",
        "conn_cost_min(s)",
        "conn_cost_sum(s)",
        "conn_cost_aver(s)",
        "getlogs_cost_max(s)",
        "getlogs_cost_min(s)",
        "getlogs_cost_sum(s)",
        "getlogs_cost_aver(s)",
        "getlogs_rate_aver(KB/s)",
    ]

    chip_table_cells = [
        [0, 1],
        [0, 0],
        [None, None],
        [None, None],
        [0, 0],
        [0, 0],
        [None, None],
        [None, None],
        [0, 0],
        [0, 0],
        [0, 0],
    ]

    for mac, v in devices.items():
        keys = ["3 -> 2", "2 -> 1"]

        for key in keys:
            if key in v:
                success_task = v[key][-1]
                chip_id = success_task["chip"]
                conn_cost = (
                    success_task["exec_connect_end_ts"]
                    - success_task["exec_connect_start_ts"]
                )
                getlogs_cost = (
                    success_task["exec_data_end_ts"]
                    - success_task["exec_data_start_ts"]
                )

                chip_table_cells[1][chip_id] += 1

                if chip_table_cells[2][chip_id] is None:
                    chip_table_cells[2][chip_id] = conn_cost
                else:
                    chip_table_cells[2][chip_id] = max(
                        chip_table_cells[2][chip_id], conn_cost
                    )

                if chip_table_cells[3][chip_id] is None:
                    chip_table_cells[3][chip_id] = conn_cost
                else:
                    chip_table_cells[3][chip_id] = min(
                        chip_table_cells[3][chip_id], conn_cost
                    )
                chip_table_cells[4][chip_id] += conn_cost

                if chip_table_cells[6][chip_id] is None:
                    chip_table_cells[6][chip_id] = getlogs_cost
                else:
                    chip_table_cells[6][chip_id] = max(
                        chip_table_cells[6][chip_id], getlogs_cost
                    )

                if chip_table_cells[7][chip_id] is None:
                    chip_table_cells[7][chip_id] = getlogs_cost
                else:
                    chip_table_cells[7][chip_id] = min(
                        chip_table_cells[7][chip_id], getlogs_cost
                    )
                chip_table_cells[8][chip_id] += getlogs_cost

    chip_table_cells[5][0] = chip_table_cells[4][0] / chip_table_cells[1][0]
    chip_table_cells[5][1] = chip_table_cells[4][1] / chip_table_cells[1][1]

    chip_table_cells[9][0] = chip_table_cells[8][0] / chip_table_cells[1][0]
    chip_table_cells[9][1] = chip_table_cells[8][1] / chip_table_cells[1][1]

    # 1000K / average_cost
    chip_table_cells[10][0] = 1000 / chip_table_cells[9][0]
    chip_table_cells[10][1] = 1000 / chip_table_cells[9][1]

    fig.add_trace(
        go.Table(
            header=dict(
                values=chip_table_header, fill_color="paleturquoise", align="left"
            ),
            cells=dict(values=chip_table_cells, fill_color="lavender", align="left"),
        ),
        row=2,
        col=1,
    )

    fig.update_layout(height=600)

    pio.write_html(fig, file=f"{history_file}.info_table.html", auto_open=True)


def render_tasks_timeline_chart(devices, history_file):
    if not devices:
        logger.info("no devices, do nothing")
        return

    tasks_list = []

    for mac, device in devices.items():
        priority_update_str_map = {
            "3 -> 2": "[High->Medium]",
            "2 -> 1": "[Medium->Low]",
        }

        for key, val in device.items():
            priority_update_str = priority_update_str_map.get(key, None)
            if priority_update_str is not None:
                # TODO: fail retries stats
                task = val[-1]

                tasks_list.append(
                    {
                        "task": f"{mac}-{priority_update_str}",
                        "start": task["scan_ts"],
                        "end": task["exec_connect_start_ts"],
                        "stage": Stage.WAIT_IN_QUEUE,
                        "priority_stage_str": f"{priority_update_str} wait_in_queue",
                        "chip": task["chip"],
                        "cost": task["exec_connect_start_ts"] - task["scan_ts"],
                    }
                )

                tasks_list.append(
                    {
                        "task": f"{mac}-{priority_update_str}",
                        "start": task["exec_connect_start_ts"],
                        "end": task["exec_connect_end_ts"],
                        "stage": Stage.CONNECT,
                        "priority_stage_str": f"{priority_update_str} connect",
                        "chip": task["chip"],
                        "cost": task["exec_connect_end_ts"]
                        - task["exec_connect_start_ts"],
                    }
                )

                tasks_list.append(
                    {
                        "task": f"{mac}-{priority_update_str}",
                        "start": task["exec_data_start_ts"],
                        "end": task["exec_data_end_ts"],
                        "stage": Stage.GET_LOGS,
                        "priority_stage_str": f"{priority_update_str} get_logs",
                        "chip": task["chip"],
                        "cost": task["exec_data_end_ts"] - task["exec_data_start_ts"],
                    }
                )

    df = pd.DataFrame(tasks_list)
    df = df.sort_values(by=["stage", "start"], ascending=[False, True])

    unique_tasks = df["task"].drop_duplicates().tolist()

    df["task"] = pd.Categorical(df["task"], categories=unique_tasks, ordered=True)
    df["start_fmt"] = pd.to_datetime(df["start"].astype(float), unit="s")
    df["end_fmt"] = pd.to_datetime(df["end"].astype(float), unit="s")

    df_str = df.to_string(formatters={"start": "{:.6f}".format, "end": "{:.6f}".format})
    logger.info(f"\n{df_str}")

    fig = px.timeline(
        df,
        x_start="start_fmt",
        x_end="end_fmt",
        y="task",
        color="priority_stage_str",
        color_discrete_map=COLOR_MAP,
        hover_data=["chip", "cost"],
        # facet_row="chip", # 拆分chip显示2个
        pattern_shape="chip",
        category_orders={"task": unique_tasks},
    )

    fig.update_xaxes(
        tickmode="linear",
        dtick=1000,
        ticklabelstep=5,
        tickformat="%Y-%m-%d %H:%M:%S.%L",
        showgrid=True,
        tickangle=45,
    )

    fig.update_yaxes(
        tickmode="array",
        tickvals=unique_tasks,
        ticktext=unique_tasks,
        showgrid=True,
    )

    fig.update_layout(
        title_text="Devices Task Timeline Chart",
        title_x=0,
        height=600,
    )

    pio.write_html(
        fig, file=f"{history_file}.tasks_timeline_chart.html", auto_open=True
    )


def render(history_file):
    logger.info(f"history json file path: {history_file}")

    with open(history_file, "r", encoding="utf-8") as f:
        json_str = f.read()

        json_data = json.loads(json_str)
        render_info_table(json_data, history_file)

        devices = json_data["history"][0]["devices"]
        render_tasks_timeline_chart(devices, history_file)


if __name__ == "__main__":
    history_file = None

    if len(sys.argv) > 1:
        history_file = sys.argv[1]

    if history_file is None:
        logger.warning(
            "Usage: python3 render_history_json ./test_devices_yyyymmddhhMMss.json"
        )
        exit()

    render(history_file)

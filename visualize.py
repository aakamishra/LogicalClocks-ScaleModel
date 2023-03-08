import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as plt_colors
import os


def read_csvs(base_dir):
    dfs = {}
    speeds = {}
    for i in range(1, 4):
        df = pd.read_csv(os.path.join(base_dir, f"{i}.csv"), index_col=False)
        df.rename(columns={df.columns[1]: 'System Time'}, inplace=True)
        desc = df.iloc[0]["Description"]
        desc = desc[desc.index("speed:"):]
        desc = desc[7:desc.index(")")]
        speed = int(desc)
        df = df.iloc[1:]
        dfs[i] = df
        speeds[i] = speed
    return dfs, speeds

def simple_system_vs_logical_plot(base_dir):
    dfs, speeds = read_csvs(base_dir)
    plt.figure(figsize=(12, 5))

    colormap = {
        "SEND": 'r',
        "RECEIVED": 'b',
        "INTERNAL": 'g'
    }
    markers = ['o', '^', 's']

    for i in range(3, 0, -1):
        colors = [colormap[x] for x in (dfs[i]["Event Type"].tolist())]
        # plt.scatter(dfs[i]["System Time"], dfs[i]["Clock Counter"], label=f"Process {i}, Speed {speeds[i]}", alpha=0.3, c=colors, marker=markers[i - 1])
        plt.plot(dfs[i]["System Time"], dfs[i]["Clock Counter"], label=f"Process {i}, Speed {speeds[i]}")

    plt.xlabel("System Time")
    plt.ylabel("Logical Clock Time")
    plt.legend()
    plt.savefig(os.path.join(base_dir, "simple.png"))
    plt.close()

plt.figure(figsize=(12, 5))

def logical_clock_jumps_plot(base_dir):
    dfs, speeds = read_csvs(base_dir)
    colormap = {
        1: 'r',
        2: 'b',
        3: 'g'
    }
    markers = ['o', '^', 's']
    
    for i in range(1, 4, 1):
        # colors = [colormap[x] for x in (dfs[i]["Event Type"].tolist())]
        plt.scatter(dfs[i]["System Time"][:-1], np.diff(dfs[i]["Clock Counter"]), label=f"Process {i}, Speed {speeds[i]}", alpha=0.5, c=colormap[i])

    plt.xlabel("System Time")
    plt.ylabel("Logical Clock Time Jump")
    plt.legend()
    plt.savefig(os.path.join(base_dir, "jumps.png"))
    plt.close()

def send_receive_plot(base_dir):
    dfs, speeds = read_csvs(base_dir)
    start_time = min([x['System Time'].iloc[0] for x in dfs.values()])
    # print("Start Time", start_time)
    plt.figure(figsize=(8, 12))
    dfs[4] = dfs[1]
    for idx in range(2):
        plt.subplot(1, 2, idx+1)
        plt.xticks(ticks=[1, 2, 3, 4], labels=[f"Process {i}\nSpeed {speeds[i]}" for i in [1, 2, 3, 1]])
        plt.ylabel("System Time")
        plt.xlabel("Process")
        pairs = [[(1, 2), (2, 3), (3, 4)], [(2, 1), (3, 2), (4, 3)]][idx]
        for p1, p2 in pairs:
            df1, df2 = dfs[p1], dfs[p2]
            sends = (start_time - df1[(df1['Event Type'] == "SEND") & (df1['Reciever'] == f'{(p2 - 1) % 3 + 1}')]["System Time"]).tolist()
            receives = (start_time - df2[(df2['Event Type'] == "RECEIVED") & (df2['Sender'] == f'{(p1 - 1) % 3 + 1}')]["System Time"]).tolist()

            # print(f"{p1} {p2} Num Sends: {len(sends)}", f"Num Recs: {len(receives)}")

            num_receives = len(receives)
            marker = ['>', '<'][idx]
            for k in range(num_receives):
                plt.plot([p1, p2], [sends[k], receives[k]], marker = marker, color='b', markevery=[1])

        for i in range(1, 5):
            colors = (np.array([int(x) for x in dfs[i]["Queue Length"].tolist()]) + 5)
            norm = plt_colors.Normalize(vmin=0, vmax=15)
            plt.scatter(i * np.ones(len(dfs[i])), start_time - dfs[i]["System Time"], c=colors, norm=norm, cmap='Reds')

    plt.savefig(os.path.join(base_dir, "full_vis.png"))
    plt.close()

if __name__ == "__main__":
    dirs = [os.path.join("logs", d) for d in os.listdir('logs')]
    for dr in dirs:
        simple_system_vs_logical_plot(dr)
        logical_clock_jumps_plot(dr)
        send_receive_plot(dr)

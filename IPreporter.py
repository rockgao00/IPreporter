# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
import socket
import threading
import csv

class MinerRackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("矿机货架位置登记")

        # 设置窗口大小为400x400
        self.root.geometry('400x400')
        # 居中窗口
        self.center_window()

        # 创建一个框架用于放置机房、货架、层数、位置
        frame = tk.Frame(root)
        frame.pack(pady=10, padx=10)

        tk.Label(frame, text="机房:").grid(row=0, column=0, padx=5)
        self.rack_room = tk.Entry(frame, width=3)
        self.rack_room.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="货架:").grid(row=0, column=2, padx=5)
        self.rack_shelf = tk.Entry(frame, width=3)
        self.rack_shelf.grid(row=0, column=3, padx=5)

        tk.Label(frame, text="层数:").grid(row=0, column=4, padx=5)
        self.rack_layer = tk.Entry(frame, width=3)
        self.rack_layer.grid(row=0, column=5, padx=5)

        tk.Label(frame, text="位置:").grid(row=0, column=6, padx=5)
        self.rack_position = tk.Entry(frame, width=3)
        self.rack_position.grid(row=0, column=7, padx=5)

        # 创建按钮框架
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        self.start_button = tk.Button(button_frame, text=" Start ", command=self.toggle_listener)
        self.start_button.grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text=" Skip ", command=self.skip_entry).grid(row=0, column=1, padx=25)
        tk.Button(button_frame, text="Export", command=self.export_data).grid(row=0, column=2, padx=35)
        tk.Button(button_frame, text="Delete", command=self.delete_selected).grid(row=0, column=3, pady=25)

        # 列表框显示信息
        self.listbox = tk.Listbox(root, width=60, height=20)
        self.listbox.pack(pady=20)

        # 初始化数据
        self.miner_data = []
        self.listener_running = False
        self.sock = None  # 初始化套接字为None

    def center_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 400) // 2
        self.root.geometry(f'400x400+{x}+{y}')

    def toggle_listener(self):
        if not self.listener_running:
            # 开始监听
            self.listener_running = True
            self.start_button.config(text="Stop", bg="red")
            threading.Thread(target=self.start_udp_listener, daemon=True).start()
        else:
            # 停止监听
            self.listener_running = False
            if self.sock:
                self.sock.close()  # 关闭套接字
                self.sock = None
            self.start_button.config(text="Start", bg="SystemButtonFace")
            print("关闭端口14235，关闭监听。")

    def start_udp_listener(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(('0.0.0.0', 14235))  # 尝试绑定端口14235
            print("端口14235绑定成功，开始监听数据。")

            while self.listener_running:
                data, addr = self.sock.recvfrom(1024)
                message = data.decode('utf-8')

                # 提取 IP 和 MAC 地址
                ip, mac = self.extract_ip_mac(message)
                room = self.rack_room.get()
                shelf = self.rack_shelf.get()
                layer = self.rack_layer.get()
                position = self.rack_position.get()

                if ip and mac:
                    # 检查是否已有相同 MAC 数据
                    if (not any(mac == item[5] for item in self.miner_data)
                        and not any(room == item[0] and shelf == item[1] and layer == item[2] and position == item[3] for item in self.miner_data)):
                        self.current_ip = ip
                        self.current_mac = mac

                        # 弹出确认对话框
                        response = messagebox.askyesno("确认", f"是否添加 {ip} {mac} 到信息栏？")
                        if response is True:
                            miner_info = f"{room}-{shelf}-{layer}-{position} {ip} {mac}"
                            self.listbox.insert(tk.END, miner_info)
                            self.miner_data.append((room, shelf, layer, position, ip, mac))
                            self.increment_position()
                        elif response is False:
                            self.current_ip = None
                            self.current_mac = None
                            pass

        except OSError:
            self.listener_running = False
            self.start_button.config(text="Start", bg="SystemButtonFace")
    #staticmethod用于修饰类中的方法,使其可以在不创建类实例的情况下调用方法，这样做的好处是执行效率比较高。
    @staticmethod
    def extract_ip_mac(message):
        try:
            # 假设格式为 '192.168.12.49,D6:A9:D1:97:CB:47'
            parts = message.split(",")
            if len(parts) == 2:
                ip, mac = message.split(",")
                return ip.strip(), mac.strip()
            return None, None
        except ValueError:
            return None, None

    def skip_entry(self):
        room = self.rack_room.get()
        shelf = self.rack_shelf.get()
        layer = self.rack_layer.get()
        position = self.rack_position.get()

        ip = 'null'
        mac = 'null'

        miner_info = f"{room}-{shelf}-{layer}-{position} {ip} {mac}"

        self.listbox.insert(tk.END, miner_info)
        self.miner_data.append((room, shelf, layer, position, ip, mac))

        self.increment_position()  # 位置自动加1

    def increment_position(self):
        try:
            current_position = int(self.rack_position.get())
            self.rack_position.delete(0, tk.END)
            self.rack_position.insert(0, str(current_position + 1))
        except ValueError:
            self.rack_position.insert(0, "1")  # 如果位置为空或不是数字，从1开始

    def export_data(self):
        with open("miner_data.csv", mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Position", "MAC"])  # 写入标题
            for item in self.miner_data:
                room, shelf, layer, position, ip, mac = item
                miner_info = f"{room}-{shelf}-{layer}-{position}"
                writer.writerow([miner_info, mac])  # 将格式化后的信息写入文件
        messagebox.showinfo("Info", "登记文件已导出")

    def delete_selected(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            # 删除列表框中选中的条目
            index = selected_index[0]
            self.listbox.delete(index)
            # 同时删除 miner_data 中对应的数据
            del self.miner_data[index]

if __name__ == "__main__":
    root = tk.Tk()#创建Tk窗口
    app = MinerRackApp(root)#初始化类实例并将root传递给它
    root.mainloop()#启动主事件循环
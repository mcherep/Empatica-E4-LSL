# Manuel Cherep <mcherep@mit.edu>
# Original code from https://github.com/HectorCarral/Empatica-E4-LSL

""" Connect to the E4 server, subscribe to data streams and stream """

import argparse
import socket
import time
import pylsl


def connect(scket, device, address, port, buffer_size):
    print("Connecting to server...")
    scket.connect((address, port))

    print("Devices available:")
    scket.send("device_list\r\n".encode())
    response = scket.recv(buffer_size)
    print(response.decode("utf-8"))

    print("Connecting to device...")
    scket.send(("device_connect " + device + "\r\n").encode())
    response = scket.recv(buffer_size)
    print(response.decode("utf-8"))

    print("Pausing data receiving...")
    scket.send("pause ON\r\n".encode())
    response = scket.recv(buffer_size)
    print(response.decode("utf-8"))


def subscribe_to_data(scket, buffer_size):
    print("Suscribing to streams...")

    scket.send(("device_subscribe " + 'acc' + " ON\r\n").encode())
    response = scket.recv(buffer_size)
    print(response.decode("utf-8"))
    scket.send(("device_subscribe " + 'bvp' + " ON\r\n").encode())
    response = scket.recv(buffer_size)
    print(response.decode("utf-8"))
    scket.send(("device_subscribe " + 'gsr' + " ON\r\n").encode())
    response = scket.recv(buffer_size)
    print(response.decode("utf-8"))
    scket.send(("device_subscribe " + 'tmp' + " ON\r\n").encode())
    response = scket.recv(buffer_size)
    print(response.decode("utf-8"))

    print("Resuming data receiving...")
    scket.send("pause OFF\r\n".encode())
    response = scket.recv(buffer_size)
    print(response.decode("utf-8"))


def prepare_LSL_streaming(name):
    print("Starting LSL streaming")
    # TODO: IDs must be unique
    outlet_acc = pylsl.StreamOutlet(pylsl.StreamInfo('acc' + '_' + name,  # name
                                                     'acc',  # category
                                                     3,  # channels
                                                     32,  # frequency
                                                     'int32',  # type
                                                     'ACC-e4' + '_' + name))  # id
    outlet_bvp = pylsl.StreamOutlet(pylsl.StreamInfo('bvp' + '_' + name,  # name
                                                     'bvp',  # category
                                                     1,  # channels
                                                     64,  # frequency
                                                     'float32',  # type
                                                     'BVP-e4' + '_' + name))  # id
    outlet_gsr = pylsl.StreamOutlet(pylsl.StreamInfo('gsr' + '_' + name,  # name
                                                     'gsr',  # category
                                                     1,  # channels
                                                     4,  # frequency
                                                     'float32',  # type
                                                     'GSR-e4' + '_' + name))  # id
    outlet_tmp = pylsl.StreamOutlet(pylsl.StreamInfo('tmp' + '_' + name,  # name
                                                     'tmp',  # category
                                                     1,  # channels
                                                     4,  # frequency
                                                     'float32',  # type
                                                     'Tmp-e4' + '_' + name))  # id
    return outlet_acc, outlet_bvp, outlet_gsr, outlet_tmp


def reconnect(scket,
              device,
              address,
              port,
              buffer_size,
              outlet_acc,
              outlet_bvp,
              outlet_gsr,
              outlet_tmp):
    print("Reconnecting...")
    connect(scket, device, address, port, buffer_size)
    subscribe_to_data(scket, buffer_size)
    stream(scket, buffer_size, outlet_acc, outlet_bvp, outlet_gsr, outlet_tmp)


def stream(scket, buffer_size, outlet_acc, outlet_bvp, outlet_gsr, outlet_tmp):
    try:
        print("Streaming...")
        while True:
            try:
                response = scket.recv(buffer_size).decode("utf-8")
                if "connection lost to device" in response:
                    print(response.decode("utf-8"))
                    reconnect(outlet_acc, outlet_bvp, outlet_gsr, outlet_tmp)
                    break
                samples = response.split("\n")
                for i in range(len(samples)-1):
                    stream_type = samples[i].split()[0]
                    if stream_type == "E4_Acc":
                        data = [int(samples[i].split()[2].replace(',', '.')),
                                int(samples[i].split()[3].replace(',', '.')),
                                int(samples[i].split()[4].replace(',', '.'))]
                        outlet_acc.push_sample(data)
                    elif stream_type == "E4_Bvp":
                        data = [float(samples[i].split()[2].replace(',', '.'))]
                        outlet_bvp.push_sample(data)
                    elif stream_type == "E4_Gsr":
                        data = [float(samples[i].split()[2].replace(',', '.'))]
                        outlet_gsr.push_sample(data)
                    elif stream_type == "E4_Temperature":
                        data = [float(samples[i].split()[2].replace(',', '.'))]
                        outlet_tmp.push_sample(data)
            except socket.timeout:
                print("Socket timeout")
                reconnect(outlet_acc, outlet_bvp, outlet_gsr, outlet_tmp)
                break
    except KeyboardInterrupt:
        print("Disconnecting from device...")
        scket.send("device_disconnect\r\n".encode())
        scket.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--address', type=str, default='127.0.0.1',
                        required=False)
    parser.add_argument('--port', type=int, default=28000,
                        required=False)
    parser.add_argument('--buffer_size', type=int, default=4096,
                        required=False)
    parser.add_argument('--device', type=str,
                        required=True)
    parser.add_argument('--name', type=str, default='',
                        required=False)

    args = parser.parse_args()

    scket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    scket.settimeout(3)

    # Connect to the E4 server
    connect(scket, args.device, args.address, args.port, args.buffer_size)
    time.sleep(1)

    # Subscribe to the data streams
    subscribe_to_data(scket, args.buffer_size)

    # Prepare LSL streaming
    out_acc, out_bvp, out_gsr, out_tmp = prepare_LSL_streaming(args.name)
    time.sleep(1)

    # Start streaming
    stream(scket, args.buffer_size, out_acc, out_bvp, out_gsr, out_tmp)


if __name__ == "__main__":
    main()

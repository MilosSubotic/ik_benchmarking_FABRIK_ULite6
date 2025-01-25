#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import shutil
import yaml
from ament_index_python.packages import get_package_share_directory

import subprocess

import rclpy
from rclpy.node import Node


def load_benchmarking_config(ik_benchmarking_pkg, ik_benchmarking_config):
    # Construct the configuration file path
    file_path = os.path.join(
        get_package_share_directory(ik_benchmarking_pkg),
        "config",
        ik_benchmarking_config,
    )

    # Open config file and parse content related to only ik_solvers
    with open(file_path, "r") as config_file:
        config_data = yaml.safe_load(config_file)

    ik_solvers_data = config_data.get("ik_solvers")

    if ik_solvers_data is None:
        raise ValueError("Missing required configuration key 'ik_solvers'")

    ik_solver_names = [ik_value.get("name") for ik_value in ik_solvers_data]

    return ik_solver_names

def main():
    # Print the path where the resulting files will be saved
    rclpy.init(args=None)
    node = Node("data_generator_node")
    node.declare_parameter("data_directory", os.getcwd())
    data_directory = (
        node.get_parameter("data_directory").get_parameter_value().string_value
    )

    print(f"\n{'=' * 60}")
    print(
        f"\nThe benchmarking CSV files will be saved in the directory:\n\n{data_directory}"
    )
    print(f"\n{'=' * 60}")

    os.makedirs(data_directory, exist_ok = True)

    # Load IK solvers data from ik_benchmarking.yaml file
    ik_benchmarking_pkg = "ik_benchmarking"
    ik_benchmarking_config = "ik_benchmarking.yaml"
    ik_solver_names = load_benchmarking_config(
        ik_benchmarking_pkg, ik_benchmarking_config
    )

    # Check if previous resulting CSV files already exist in the current directory
    current_csv_filenames = glob.glob(os.path.join(data_directory, "*.csv"))
    result_csv_filenames = [
        os.path.join(data_directory, ik_solver_name + "_ik_benchmarking_data.csv")
        for ik_solver_name in ik_solver_names
    ]
    conflict_csv_filenames = []

    if current_csv_filenames:
        for filename in current_csv_filenames:
            if filename in result_csv_filenames:
                conflict_csv_filenames.append(filename)

    if conflict_csv_filenames:
        print(
            "Warning: The current directory contains IK benchmarking files from previous runs: "
        )
        print(", ".join(conflict_csv_filenames))
        user_input = input(
            "\nDo you want to permanently delete them and continue the benchmarking? (y/n): "
        )

        if user_input.lower() == "y":
            for filename in conflict_csv_filenames:
                os.remove(filename)

            print("Conflicting CSV files deleted. Continuing with benchmarking...\n")

        elif user_input.lower() == "n":
            print("Benchmarking aborted.")
            exit(0)

        else:
            print("Invalid input. Benchmarking aborted.")
            exit(1)

    # Commands to run ik benchmarking with different IK solvers
    launch_commands = [
        f"ros2 launch ik_benchmarking start_ik_benchmarking.launch.py ik_solver_name:={ik_solver_name}"
        for ik_solver_name in ik_solver_names
    ]

    for command in launch_commands:
        process = subprocess.Popen(command, shell=True, executable="/bin/bash")

        # Wait indefinitely for completion to ensure sequential processing
        process.communicate()

        # Copy result csv to data directory.
        for csv in glob.glob("*_ik_benchmarking_data.csv"):
            shutil.move(csv, data_directory)


if __name__ == "__main__":
    main()

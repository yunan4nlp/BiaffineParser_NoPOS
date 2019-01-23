nohup python3 -u driver/TrainTest.py --config_file ctb.parser.cfg --thread 1 --use-cuda > log 2>&1 &
tail -f log

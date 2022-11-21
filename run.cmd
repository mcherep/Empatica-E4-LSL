@echo off

echo Checking if conda env exists...
call conda activate e4-lsl
if errorlevel 1 (
   echo.
   echo Creating conda environment...
   call conda env create -n e4-lsl -f env.yml
)

echo Run application...
call conda activate e4-lsl && python empatica-e4-LSL.py --device %1 --name %2

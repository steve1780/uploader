echo "Bootscript  starting .."
sudo pigpiod &
echo "pigiod running"
python /home/pi/esp_loader/uploader2.py


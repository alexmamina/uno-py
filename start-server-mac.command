ip=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | cut -d\  -f2)
echo "INPUT PORT NUMBER (or press ENTER if you'd like to use the default 44444)"

read port

if [ -z "$port" ]
then 
	port=44444
fi

echo HOW MANY PLAYERS ARE THERE GOING TO BE?
read numplayers


echo WHAT MODES WOULD YOU LIKE TO USE?
echo "Enter numbers, without spaces (or press ENTER if you don't want any)"
echo 1. 7/0
echo 2. Stack +2
echo 3. Take many cards

read modes

if [ -z "$modes" ]
then 
	modes="0"
fi


echo CONNECT TO:
echo $ip $port

cd
cd Downloads/uno-py-master
#python server.py $ip $port $numplayers $modes
python3 server.py $ip $port $numplayers $modes

# Call the AdviceSlip API and save output as JSON
curl -s https://api.adviceslip.com/advice > advice.json
cat advice.json | jq -r '.slip.advice' > advice.message

# Ensure the advice has more than 5 words
#[ $(wc -w < advice.message) -gt 5 ] && echo "Advice has more than 5 words" || (echo "Advice - $(cat advice.message) has 5 words or less")

# Install cowsay (if not already installed) and generate ASCII artwork
sudo apt-get install cowsay -y > /dev/null 2>&1
#echo $PATH
export PATH="$PATH:/usr/games:/usr/local/games"
cat advice.message | cowsay -f $(ls /usr/share/cowsay/cows | shuf -n 1)

rm advice.json advice.message
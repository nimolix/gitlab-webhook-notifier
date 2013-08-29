## gitlab-webhook-notifier

### Intro
Simple script for gitlab to notify team members by email after push event

### Prerequisite

```bash
$ pip install requests
```

### Configuration

Open the script and near the top you'll find the following lines:
<pre>
# log file
log_file = './gitlab-notifier.log'

# gitlab installation url
gitlab_url = 'http://gitlab.local'

# api access token, get it from your profile page in gitlab
gitlab_token = ''

# smtp host, defaults to 'localhost'
smtp_host = 'localhost'

# smtp username, leave it empty if you're submitting to localhost
smtp_user = ''

# smtp password, leave it empty if you're submitting to localhost
smtp_pass = ''

# from part of the mail
mail_from = 'gitlab@gitlab.local'

# bind the notifier to this port
bind_port = 8000

# when rotate log file
log_max_size = 5 * pow(2, 20)         # 5MB

# verbosity level
log_level = logging.INFO
</pre>

Fire up a tmux/screen session and execute the script

Setup your project in gitlab accordingly!


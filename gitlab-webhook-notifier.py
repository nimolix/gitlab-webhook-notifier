#!/usr/bin/python -tt
#
# Copyright (C) 2013 Nima Shayafar <nima@shayafar.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# gitlab-webhook-notifier: a script for gitlab to notify team members after push
#
# Grab the latest updates from my github repo:
# https://github.com/nimolix/gitlab-webhook-notifier

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import logging.handlers
import requests
import smtplib
from string import Template


##### configuration starts here #####

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

# when to rotate log file
log_max_size = 5 * pow(2, 20)         # 5MB

# verbosity level
log_level = logging.INFO
#log_level = logging.DEBUG      # DEBUG is quite verbose

##### You should stop changing things unless you know what you are doing #####
##############################################################################

log = logging.getLogger('log')
log.setLevel(log_level)
log_handler = logging.handlers.RotatingFileHandler(log_file,
                                                   maxBytes=log_max_size,
                                                   backupCount=4)
f = logging.Formatter("%(asctime)s %(filename)s %(levelname)s %(message)s",
                      "%B %d %H:%M:%S")
log_handler.setFormatter(f)
log.addHandler(log_handler)


class Receiver(BaseHTTPRequestHandler):

    def do_POST(self):
        log.debug('serving request...')
        message = 'OK'
        self.rfile._sock.settimeout(5)
        request_body = self.rfile.read(int(self.headers['Content-Length']))
        self.send_response(200)
        self.send_header('Content-type', 'text')
        self.send_header('Content-length', str(len(message)))
        self.end_headers()
        self.wfile.write(message)
        log.debug('closed gitlab connection.')
        # parse data
        push_info = json.loads(request_body)

        project_name = push_info['repository']['name']
        project_url = push_info['repository']['homepage']
        user_name = push_info['user_name']
        commits = push_info['commits']

        api_endpoint = '%s/api/v3' % gitlab_url
        headers = {'PRIVATE-TOKEN': gitlab_token}

        # get list of projects
        r = requests.get(api_endpoint + '/projects', headers=headers)
        projects = r.json()
        log.debug('got the projects list.')
        project_id = None
        for project in projects:
            if project['name'] == project_name:
                project_id = project['id']
                break

        if project_id is None:
            log.info('Project %s does not exist!' % project_name)
            return

        # get team members of the project
        r = requests.get('%s/projects/%d/members' % (api_endpoint, project_id), headers=headers)
        members = r.json()
        log.debug('got the project members.')

        # composing email
        mail_subject = 'GitLab | %s | notify' % project_name
        commit_log = ''
        for commit in commits:
            commit_log += ' - by %s <%s>\n' % (commit['author']['name'], commit['author']['email'])
            commit_log += '   %s\n\n' % commit['message']

        mail_template = Template('''
$user_name pushed new commits to $project_name.

* Project page
- $project_url

* Commit info
$commit_log
----
This email is delivered by GitLab Web Hook.
        ''')
        mail_body = mail_template.substitute(locals())
        member_emails = [m['email'] for m in members]

        payload = '\r\n'.join(
            (
                'From: %s' % mail_from,
                'To: %s' % ','.join(member_emails),
                'Subject: %s' % mail_subject,
                '',
                mail_body
            )
        )
        log.debug('preparing to send email.')
        # trying to send email
        server = smtplib.SMTP(smtp_host)
        if smtp_user and smtp_pass:
            log.debug('login to the smtp server.')
            server.login(smtp_user, smtp_pass)

        server.sendmail(mail_from, member_emails, payload)
        log.debug('message sent successfully!')
        server.quit()

    def log_message(self, format, *args):
        """
            disable printing to stdout/stderr for every request
        """
        return


def main():
    try:
        server = HTTPServer(('', bind_port), Receiver)
        log.info('started web server...')
        server.serve_forever()
    except KeyboardInterrupt:
        log.info('ctrl-c pressed, shutting down.')
        server.socket.close()

if __name__ == '__main__':
    main()

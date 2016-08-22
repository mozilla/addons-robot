import time
import re

import irc.bot

channel = '#amo-bots'
nickname = 'addons-robot'
server = 'irc.mozilla.org'


class TestBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

    def on_welcome(self, c, e):
        c.join(self.channel)
        for msg in self.msgs:
            self.connection.privmsg(self.channel, msg)

        time.sleep(1)
        self.die()


def notify_irc(*msgs):
    bot = TestBot(channel, nickname, server)
    if isinstance(msgs, str):
        msgs = [msgs]
    bot.msgs = msgs
    try:
        bot.start()
    except SystemExit:
        print 'exiting'


def parse_link_headers(header):
    if not header:
        return {}

    rx = '\<(.*?)>; rel="(\w+)"(?:,)'
    return dict([(v, k) for k, v in re.findall(rx, header)])


if __name__=='__main__':
    notify_irc('some test', 'messages')

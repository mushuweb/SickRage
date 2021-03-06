# coding=utf-8

import sickbeard

from sickbeard import logger, common
from pynma import pynma


class Notifier(object):
    def test_notify(self, nma_api, nma_priority):
        return self._sendNMA(nma_api, nma_priority, event="Test", message="Testing NMA settings from Medusa",
                             force=True)

    def notify_snatch(self, ep_name, is_proper):
        if sickbeard.NMA_NOTIFY_ONSNATCH:
            self._sendNMA(nma_api=None, nma_priority=None, event=common.notifyStrings[(common.NOTIFY_SNATCH, common.NOTIFY_SNATCH_PROPER)[is_proper]],
                          message=ep_name)

    def notify_download(self, ep_name):
        if sickbeard.NMA_NOTIFY_ONDOWNLOAD:
            self._sendNMA(nma_api=None, nma_priority=None, event=common.notifyStrings[common.NOTIFY_DOWNLOAD],
                          message=ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.NMA_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._sendNMA(nma_api=None, nma_priority=None, event=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD],
                          message=ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_NMA:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._sendNMA(nma_api=None, nma_priority=None, event=title, message=update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_NMA:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._sendNMA(nma_api=None, nma_priority=None, event=title, message=update_text.format(ipaddress))

    def _sendNMA(self, nma_api=None, nma_priority=None, event=None, message=None, force=False):

        title = 'Medusa'

        if not sickbeard.USE_NMA and not force:
            return False

        if nma_api is None:
            nma_api = sickbeard.NMA_API

        if nma_priority is None:
            nma_priority = sickbeard.NMA_PRIORITY

        batch = False

        p = pynma.PyNMA()
        keys = nma_api.split(',')
        p.addkey(keys)

        if len(keys) > 1:
            batch = True

        logger.log(u"NMA: Sending notice with details: event=\"%s\", message=\"%s\", priority=%s, batch=%s" % (event, message, nma_priority, batch), logger.DEBUG)
        response = p.push(application=title, event=event, description=message, priority=nma_priority, batch_mode=batch)

        if not response[nma_api][u'code'] == u'200':
            logger.log(u'Could not send notification to NotifyMyAndroid', logger.ERROR)
            return False
        else:
            logger.log(u"NMA: Notification sent to NotifyMyAndroid", logger.INFO)
            return True

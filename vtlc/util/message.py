def convertRawMessageToString(rawMessage):

    def handler(run):
        msgType = list(run.keys())[0]
        payload = run[msgType]
        if msgType == 'text':
            return payload
        elif msgType == 'emoji':
            if 'isCustomEmoji' in payload:
                # label = payload['image']['accessibility']['accessibilityData'][
                #     'label']
                """
                Replacement character U+FFFD
                https://en.wikipedia.org/wiki/Specials_(Unicode_block)#Replacement_character
                """
                return "\uFFFD"
            else:
                return payload['emojiId']
        else:
            raise 'Invalid type: ' + msgType + ', ' + payload

    return "".join([handler(run) for run in rawMessage])

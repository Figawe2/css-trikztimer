import es, esc, playerlib, string


hook = False

class ChatHandler:
    def __init__(self):

        # Here are all the public commands stored
        self.commands = {}

        # Here are all the private commands stored
        self.p_commands = {}

        """
        If sourcemod is set to true, sourcemod commands will now work, if executed in chat;
        like !admin, nominate etc..
        """
        self.sourcemod = False

        """ Text combinations that should be hidden for whatever reason are stored here!"""
        self.hide_text = []

        # TODO: make tags
        self.tags = {}

        self.method_name = None  # set by the command line options


    def registerPublicCommand(self, text, function_name, limit_args=False, combination=False, startswith=False):
            """
            :param text:  The text a user should write to execute this function
            :param function_name: Set a pointer to ur function, so you decide what happens when the command is executed
            :param combination:  If this is set to true, then every text combination such as (!ADMIN, !admin or both !aDmIn) will still count
            :param startswith: If this is set to true, this function will execute if the player text startswith the command u put in this function
            :return: no return value (See: chat.getPublicCommands instead)
            """
            if isinstance(text, str):
                self.commands[text] = [function_name, limit_args, combination, startswith]

            else: raise ValueError("chat.registerPublicCommand .text. => Command not a string.")


    def registerHiddenCommand(self, text, function_name, limit_args=False, combination=False, startswith=False):
            """
            :param text:  The text a user should write to execute this function
            :param function_name: Set a pointer to ur function, so you decide what happens when the command is executed
            :param combination:  If this is set to true, then every text combination such as (!ADMIN, !admin or both !aDmIn) will still count
            :param startswith: If this is set to true, this function will execute if the player text startswith the command u put in this function
            :return: no return value (See: chat.getPublicCommands instead)
            """
            if isinstance(text, str):
                self.p_commands[text] = [function_name, limit_args, combination, startswith]
            else: raise ValueError("chat.registerHiddenCommand .text. => Command not a string.")


    def deletetext(self, *args):
            for arg in args:
                self.hide_text.append(arg)

    def executeCommand(self, *args):
            pass

    def unregisterCommand(self, text):
            if isinstance(text, str):
                try:
                    del self.commands[text]
                except KeyError:
                    print("chat.registerHiddenCommand => command does not exist")
                try:
                    del self.p_commands[text]
                except KeyError:
                    print("chat.registerHiddenCommand => command does not exist")

            else: raise ValueError("chat.unregisterCommand .text. => Command not a string.")

    def getPublicCommands(self, var_dump=False):
            if var_dump:
                return self.commands
            else:
                listing = []
                for object in self.commands:
                    listing.append(object)
                return listing

    def getPrivateCommands(self, var_dump=False):
            if var_dump:
                return self.p_commands
            else:
                listing = []
                for object in self.p_commands:
                    listing.append(object)
                return listing

    def getHookfunc(self):
            return self.method_name

    def setPlayerTag(self, tag):
            if isinstance(tag, str):
                esc.msg(tag)
            else: esc.msg('[setPlayerTag] => Not a string')

    def getPlayerTags(self):
            return self.tags

    def hook(self, area, func):
        if area == "window.chat":
            # TODO: allow_sourcemod
            es.addons.registerSayFilter(hook_chat)
            if func:
                if hasattr(func, '__call__'):
                    self.method_name = func
                else: raise ValueError("chat.registerFunction .text. => Command not a string.")

        else: print('chat.hook => What you are trying to hook is not available')

    def unhook(self, area):
        if area == "window.chat":
            es.addons.unregisterSayFilter(hook_chat)
        else: print('chat.hook => What you are trying to hook is not available')


chat = ChatHandler()


def hook_chat(userid, text, teamonly):
    player = playerlib.getPlayer(userid)
    steamid = player.steamid
    name = player.name
    text = str(string.strip(text, '"'))
    re_text = text

    for object in chat.hide_text:
        if text == object:
            return (0,0,0)

    method = chat.getHookfunc()
    if hasattr(method, '__call__'):
        if method(userid, text, steamid, name, teamonly):
            return(0,0,0)


    if len(chat.getPublicCommands(True)) > 0:

        for object in chat.getPublicCommands(True):

            if chat.getPublicCommands(True)[object][2]:
                text = text.lower()
            else:
                text = re_text

            if chat.getPublicCommands(True)[object][3]:

                if text.startswith(str(object)):

                    public_func_name = chat.getPublicCommands(True)[object][0]

                    if chat.getPublicCommands(True)[object][1]:
                        public_func_name(userid)
                    else:
                        public_func_name(userid, text, steamid, name)

            elif text == str(object):
                public_func_name = chat.getPublicCommands(True)[object][0]

                if chat.getPublicCommands(True)[object][1]:
                    public_func_name(userid)
                else:
                    public_func_name(userid, text, steamid, name)

    if len(chat.getPrivateCommands(True)) > 0:

        for object in chat.getPrivateCommands(True):



                if chat.getPrivateCommands(True)[object][2]:
                    text = text.lower()
                else: text = re_text

                if chat.getPrivateCommands(True)[object][3]:


                    if text.startswith(str(object)):

                        private_func_name = chat.getPrivateCommands(True)[object][0]

                        # Set pointer to new function
                        if chat.getPrivateCommands(True)[object][1]:
                            private_func_name(userid)
                        else:
                            private_func_name(userid, text, steamid, name)

                        # Hide the message
                        return (0, 0, 0)


                elif text == str(object):

                    private_func_name = chat.getPrivateCommands(True)[object][0]

                    # Set pointer to new function
                    if chat.getPrivateCommands(True)[object][1]:
                        private_func_name(userid)
                    else:
                        private_func_name(userid, text, steamid, name)

                    # Hide the message
                    return(0,0,0)

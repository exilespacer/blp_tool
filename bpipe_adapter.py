# SubscriptionWithEventHandlerExample.py
import time
import blpapi
import zmq
from bpipe_config import BpipeHost, BpipePort
#BpipeHost = '192.168.1.1'
#BpipePort = 3333

TOKEN_SUCCESS = blpapi.Name("TokenGenerationSuccess")
TOKEN_FAILURE = blpapi.Name("TokenGenerationFailure")
AUTHORIZATION_SUCCESS = blpapi.Name("AuthorizationSuccess")
AUTHORIZATION_FAILURE = blpapi.Name("AuthorizationFailure")
TOKEN = blpapi.Name("token")


class Bpipe():
    def __init__(self, host, port, auth_string=None):
        # configure
        self.host = host
        self.port = port
        self.authenticationOptions_string = "AuthenticationMode=APPLICATION_ONLY;ApplicationAuthenticationType=APPNAME_AND_KEY;ApplicationName=rs:app"

        # initialize socket server
        self.socket = zmq.Context().socket(zmq.PAIR)
        self.socket.bind("tcp://*:%s" % 5556)

        # initialize session
        self.session = self.get_session()
        self.session.start()
        self.session.openService("//blp/mktdata")
        self.session.openService("//blp/apiauth")
        self.authService = self.session.getService("//blp/apiauth")

        # any subscription should be done by an authorized identity
        self.subscriptionIdentity = self.session.createIdentity()

    def __call__(self, codes, fields):
        self.authorize()
        self.sub(codes, fields)
        time.sleep(86400)

    def get_session(self):
        sessionOptions = blpapi.SessionOptions()
        sessionOptions.setServerAddress(self.host, self.port, 0)
        sessionOptions.setAuthenticationOptions(self.authenticationOptions_string)
        sessionOptions.setAutoRestartOnDisconnection(True)
        session = blpapi.Session(sessionOptions, self.processEvent)# callback
        return session

    def authorize(self):
        authEventQueue =blpapi.EventQueue()

        authRequest = self.authService.createAuthorizationRequest()
        authRequest.set(TOKEN, self.get_token())
        self.session.sendAuthorizationRequest(authRequest,
                                              self.subscriptionIdentity,
                                              blpapi.CorrelationId("auth"),
                                              authEventQueue)

        # examine if there's a AuthorizationFailure
        event = authEventQueue.nextEvent()
        authority_status = blpapi.event.MessageIterator(event).next().messageType()
        if authority_status == AUTHORIZATION_FAILURE:
            raise Exception("Failed to authorize.")

    def get_token(self):
        tokenEventQueue = blpapi.EventQueue()

        self.session.generateToken(eventQueue=tokenEventQueue)
        event = tokenEventQueue.nextEvent()
        token = blpapi.event.MessageIterator(event).next().getElementAsString(TOKEN)

        # examine if there's a TokenGenerationFailure
        token_generate_status = blpapi.event.MessageIterator(event).next().messageType()
        if token_generate_status == TOKEN_FAILURE:
            raise Exception("Failed to get token")

        return token

    def sub(self, codes, fields):
        subscriptions = blpapi.SubscriptionList()
        [subscriptions.add(code, fields, correlationId=blpapi.CorrelationId(code)) for code in codes]
        self.session.subscribe(subscriptions, self.subscriptionIdentity)

    def processEvent(self, event, session):
        msg = blpapi.event.MessageIterator(event).next()
        self.socket.send_pyobj(str(msg))

bpipe = Bpipe(host=BpipeHost, port=BpipePort)
if __name__ == '__main__':
    bpipe(['2330 TT Equity'], ['event_time', 'last_price'])
    pass


import grpc

import rfcontrol_pb2_grpc
import rfcontrol_pb2


class Greeter(Greeter):
    def Greet(self, request: GreetingRequest, context: grpc.ServicerContext) -> GreetingResponse:
        return GreetingResponse(greeting='Hello %s!' % request.name)

    def Chat(self, request_iterator , context: grpc.ServicerContext):
        for request in request_iterator:
            yield GreetingResponse(greeting=f"Welcome, {request.name}!")
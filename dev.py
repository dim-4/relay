""" used to manually test some functionalities """
from relay import Listener, Emitter


class User:
    def do_something(self):
        pass

    def do_something_else(self):
        pass


user = [
    Listener(handler=User.do_something, event_type="user.do_something"),
]


class MyClass:
    def __init__(self) -> None:
        self.bind 
        pass



""" NOTE

Event schema will be determined by looking at the methods in the
bindings that emit that event.
- Validation there would be to make sure all methods emitting same events
return the same data structure.

@receives([str, Audio, {str: int}])
def on_audio(self, event:Event): ...
- the validation happens in the decorator making sure that passed optional
data type parameter matches the type of the event it receives.


During the bindings initialization, we check:
1. All binded methods emitting the same event have the same return type.
2. All binded methods receiving events expect the same data type as the
return types of the methods emitting those events.
- this means we need to know the decorator params of the @receives decorator

"""


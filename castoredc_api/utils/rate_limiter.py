'''
Function decorator for rate limiting API calls. 
based on https://github.com/tomasbasham/ratelimit
'''

from functools import wraps
from math import floor
import sys
import threading
import time



class RateLimiter:
    def __init__(self, max_calls=15, period=900, raise_on_limit=True):
        '''
        Instantiate a Decorator with some sensible defaults.

        :param int max_calls: Maximum function invocations allowed within a time period.
        :param float period: An upper bound time period (in seconds) before the rate limit resets.
        :param bool raise_on_limit: A boolean allowing the caller to avoiding rasing an exception.
        '''
        self.max_calls = max(1, min(sys.maxsize, floor(max_calls)))
        self.period = period
        self.raise_on_limit = raise_on_limit

        self.last_reset = time.monotonic()
        self.num_calls = 0

        # Add thread safety.
        self.lock = threading.RLock()


    def __call__(self, func):
        '''
        Return a wrapped function that prevents further function invocations if previously called within a specified period of time.

        :param function func: The function to decorate.
        :return: Decorated function.
        :rtype: function
        '''
        @wraps(func)
        def wrapper(*args, **kargs):
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.last_reset

                # If the time window has elapsed then reset.
                if elapsed > self.period:
                    self.num_calls = 0
                    self.last_reset = time.monotonic()

                # If limit is reached: 
                if self.num_calls > self.max_calls:
                    # raise custom exception if stated.
                    if self.raise_on_limit:
                        raise RateLimitException('too many calls', self.period - elapsed)
                    # Else: Wait 
                    else:
                        sleep_time = self.period - elapsed
                        if sleep_time > 0:
                            print(f"Rate limited, sleeping for {sleep_time} seconds")
                            time.sleep(sleep_time)
           
                self.num_calls += 1

            return func(*args, **kargs)
        
        return wrapper
    

class RateLimitException(Exception):
    '''
    Rate limit exception class.
    '''
    def __init__(self, message, period_remaining):
        '''
        Custom exception raise when the number of function invocations exceeds that imposed by a rate limit.
        Additionally the exception is aware of the remaining time period after which the rate limit is reset.

        :param string message: Custom exception message.
        :param float period_remaining: The time remaining until the rate limit is reset.
        '''
        super(RateLimitException, self).__init__(message)
        self.period_remaining = period_remaining
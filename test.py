import time

# Initialize counter and start time
counter = 0
start_time = time.time()
last_time = start_time

while True:
    # Calculate elapsed time since start
    new_time = time.time()
    elapsed_time = new_time - last_time
    
    # Check if a sixth of a second has passed
    if elapsed_time >= 1/1:
        # Increment counter and reset elapsed_time
        counter += 1
        elapsed_time = 0
        last_time = new_time
        
    # Do other things in the loop, if needed
    print(counter)
    
    # Sleep for a short amount of time to prevent busy waiting
    time.sleep(0.001)
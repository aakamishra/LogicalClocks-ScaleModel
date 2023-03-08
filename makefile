all: experiment

experiment:
	for number in 1 2 3 4 5 ; do \
        python p2p_simulator.py ; \
		python visualize.py ; \
		sleep 10 ; \
    done

visualize:
	python visualize.py

clean:
	rm -r logs/logs*

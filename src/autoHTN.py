import pyhop
import json

operator_dict = {}

def check_enough(state, ID, item, num):
    if getattr(state, item)[ID] >= num:
        return []
    return False

def produce_enough(state, ID, item, num):
    return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods('have_enough', check_enough, produce_enough)

def produce(state, ID, item):
    return [('produce_{}'.format(item), ID)]

pyhop.declare_methods('produce', produce)

def make_method(name, rule):
    def method(state, ID):
        requirements = rule.get('Requires', {})
        consumables = rule.get('Consumes', {})
        tasks = []

        for item, amount in requirements.items():
            task = ('have_enough', ID, item, amount)
            tasks.append(task)

        for item, amount in consumables.items():
            task = ('have_enough', ID, item, amount)
            tasks.append(task)

        task_name = 'op_{}'.format(name)
        tasks.append((task_name, ID))

        return tasks

    return method, rule.get('Time')

def declare_methods(data):
    items = data.get("Items", [])
    tools = data.get("Tools", [])
    recipes = data.get("Recipes", {})
    for item in items:
        methods = []
        for name, rule in recipes.items():
            products = rule.get('Produces')
            if item in products.keys():
                method, time = make_method(name, rule)
                method.__name__ = '{}'.format(name)
                methods.append((method, time))
        sorted_methods = [func for func, time in sorted(methods, key=lambda x: x[1])]
        pyhop.declare_methods('produce_{}'.format(item), *sorted_methods)

    for item in tools:
        methods = []
        for name, rule in recipes.items():
            products = rule.get('Produces')
            if item in products.keys():
                method, time = make_method(name, rule)
                method.__name__ = '{}'.format(name)
                methods.append((method, time))
        sorted_methods = [func for func, time in sorted(methods, key=lambda x: x[1])]
        pyhop.declare_methods('produce_{}'.format(item), *sorted_methods)

def make_operator(name, rule):
    def operator(state, ID):
        time = rule.get('Time')
        if state.time[ID] >= time:
            products = rule.get('Produces', {})
            requirements = rule.get('Requires', {})
            consumables = rule.get('Consumes', {})

            for item, amount in requirements.items():
                state_dict = getattr(state, item, {})
                if state_dict[ID] < amount:
                    return False

            for item, amount in consumables.items():
                state_dict = getattr(state, item, {})
                if state_dict[ID] < amount:
                    return False

            for item, amount in consumables.items():
                state_dict = getattr(state, item, {})
                state_dict[ID] -= amount

            state.time[ID] -= time

            for item, amount in products.items():
                state_dict = getattr(state, item, {})
                state_dict[ID] += amount

            return state
        return False
    operator.__name__ = 'op_{}'.format(name)
    return operator

def declare_operators(data):
    recipes = data.get("Recipes", {})
    for name, rule in recipes.items():
        op_name = 'op_{}'.format(name)
        operator_dict[op_name] = make_operator(name, rule)

    pyhop.declare_operators(*operator_dict.values())

def add_heuristic(data, ID):
    def heuristic(state, curr_task, tasks, plan, depth, calling_stack):
        # Avoid cyclic dependencies by keeping track of tasks in calling_stack
        if curr_task in calling_stack:
            return True
        
        # Prune branches where time is insufficient
        if curr_task[0].startswith('op_'):
            operator_name = curr_task[0][3:]  # Remove 'op_' prefix to get the operator name
            operator_time = next((rule.get('Time') for name, rule in data['Recipes'].items() if name == operator_name), None)
            if operator_time and state.time[ID] < operator_time:
                return True
        
        # Prioritize tasks that can be completed quickly (Greedy Heuristic)
        if curr_task[0].startswith('produce'):
            item = curr_task[2]
            min_time = min(rule.get('Time') for name, rule in data['Recipes'].items() if item in rule.get('Produces', {}).keys())
            if min_time > state.time[ID]:
                return True

        # Prioritize tasks with available resources (Resource-Aware Heuristic)
        if curr_task[0] == 'produce':
            item = curr_task[2]
            for name, rule in data['Recipes'].items():
                if item in rule.get('Produces', {}):
                    requirements = rule.get('Requires', {})
                    consumables = rule.get('Consumes', {})
                    if not all(getattr(state, req_item)[ID] >= req_amount for req_item, req_amount in requirements.items()):
                        return True
                    if not all(getattr(state, cons_item)[ID] >= cons_amount for cons_item, cons_amount in consumables.items()):
                        return True

        # Early termination for tasks that are not likely to contribute towards the goal efficiently
        if curr_task[0] == 'produce':
            item = curr_task[2]
            for name, rule in data['Recipes'].items():
                if item in rule.get('Produces', {}):
                    requirements = rule.get('Requires', {})
                    consumables = rule.get('Consumes', {})
                    if any(getattr(state, req_item)[ID] < req_amount for req_item, req_amount in requirements.items()):
                        return True
                    if any(getattr(state, cons_item)[ID] < cons_amount for cons_item, cons_amount in consumables.items()):
                        return True

        return False

    pyhop.add_check(heuristic)

def set_up_state(data, ID, time=0):
    state = pyhop.State('state')
    state.time = {ID: time}

    for item in data['Items']:
        setattr(state, item, {ID: 0})

    for item in data['Tools']:
        setattr(state, item, {ID: 0})
        check = 'made_{}'.format(item)
        setattr(state, check, {ID: False})

    for item, num in data['Initial'].items():
        setattr(state, item, {ID: num})

    return state

def set_up_goals(data, ID):
    goals = []
    for item, num in data['Goal'].items():
        goals.append(('have_enough', ID, item, num))

    return goals

if __name__ == '__main__':
    rules_filename = 'crafting.json'

    with open(rules_filename) as f:
        data = json.load(f)

    state = set_up_state(data, 'agent', 300)  # Set initial time here
    goals = set_up_goals(data, 'agent')

    declare_operators(data)
    declare_methods(data)
    add_heuristic(data, 'agent')

    pyhop.print_operators()
    pyhop.print_methods()

    # Hint: verbose output can take a long time even if the solution is correct
    # try verbose=1 if it is taking too long
    result = pyhop.pyhop(state, goals, verbose=1)
    print("** result =", result)



# # working
# import pyhop
# import json

# operator_dict = {}

# def check_enough (state, ID, item, num):
# 	if getattr(state,item)[ID] >= num: return []
# 	return False

# def produce_enough (state, ID, item, num):
# 	return [('produce', ID, item), ('have_enough', ID, item, num)]

# pyhop.declare_methods ('have_enough', check_enough, produce_enough)

# def produce (state, ID, item):
# 	return [('produce_{}'.format(item), ID)]

# pyhop.declare_methods ('produce', produce)

# def make_method (name, rule):
# 	def method (state, ID):
# 		# your code here
# 		requirements = rule.get('Requires', {})
# 		consumables = rule.get('Consumes', {})
# 		tasks = []
		
# 		for item, amount in requirements.items():
# 			task = ('have_enough', ID, item, amount)
# 			tasks.append(task)
		
# 		for item, amount in consumables.items():
# 			task = ('have_enough', ID, item, amount)
# 			tasks.append(task)
		
# 		task_name = 'op_{}'.format(name)
# 		tasks.append((task_name, ID))
		
# 		return tasks
# 	return method, rule.get('Time')

# def declare_methods (data):
# 	# some recipes are faster than others for the same product even though they might require extra tools
# 	# sort the recipes so that faster recipes go first

# 	# your code here
# 	# hint: call make_method, then declare the method to pyhop using pyhop.declare_methods('foo', m1, m2, ..., mk)	
# 	items = data.get("Items", [])
# 	tools = data.get("Tools", {})
# 	recipes = data.get("Recipes", {})
# 	for item in items:
# 		methods = []
# 		for name, rule in recipes.items():
# 			products = rule.get('Produces')
# 			if item in products.keys():
# 				method, time = make_method(name, rule)
# 				method.__name__ = '{}'.format(name)
# 				methods.append((method, time))
# 		sorted_methods = [func for func, time in sorted(methods, key=lambda x: x[1])]
# 		pyhop.declare_methods ('produce_{}'.format(item), *sorted_methods)
	
# 	for item in tools:
# 		methods = []
# 		for name, rule in recipes.items():
# 			products = rule.get('Produces')
# 			if item in products.keys():
# 				method, time = make_method(name, rule)
# 				method.__name__ = '{}'.format(name)
# 				methods.append((method, time))
# 		sorted_methods = [func for func, time in sorted(methods, key=lambda x: x[1])]
# 		pyhop.declare_methods ('produce_{}'.format(item), *sorted_methods)


# def make_operator (name, rule):
# 	def operator (state, ID):
# 		# your code here
# 		time = rule.get('Time')
# 		if state.time[ID] >= time:
# 			products = rule.get('Produces', {})
# 			requirements = rule.get('Requires', {})
# 			consumables = rule.get('Consumes', {})

# 			# Check requirements and consumable are met
# 			for item, amount in requirements.items():
# 				state_dict = getattr(state, item, {}) 
# 				if state_dict[ID] < amount:
# 					return False
			
# 			for item, amount in consumables.items():
# 				state_dict = getattr(state, item, {})
# 				if state_dict[ID] < amount:
# 					return False
			
# 			# Deduct consumables
# 			for item, amount in consumables.items():
# 				state_dict = getattr(state, item, {})
# 				state_dict[ID] -= amount
			
# 			# Deduct time
# 			state.time[ID] -= time
			
# 			# Add produced goods
# 			for item, amount in products.items():
# 				state_dict = getattr(state, item, {})
# 				state_dict[ID] += amount
			
# 			return state
# 		return False
# 	operator.__name__ = 'op_{}'.format(name)
# 	return operator

# def declare_operators (data):
# 	# your code here
# 	recipes = data.get("Recipes", {})
# 	for name, rule in recipes.items():
# 		op_name = 'op_{}'.format(name)
# 		operator_dict[op_name] = make_operator(name, rule)

# 	pyhop.declare_operators (*operator_dict.values())

# def add_heuristic (data, ID):
# 	# prune search branch if heuristic() returns True
# 	# do not change parameters to heuristic(), but can add more heuristic functions with the same parameters: 
# 	# e.g. def heuristic2(...); pyhop.add_check(heuristic2)
# 	def heuristic (state, curr_task, tasks, plan, depth, calling_stack):
# 		if depth > 30:
# 			return True
# 		return False # if True, prune this branch

# 	pyhop.add_check(heuristic)


# def set_up_state (data, ID, time=0):
# 	state = pyhop.State('state')
# 	state.time = {ID: time}

# 	for item in data['Items']:
# 		setattr(state, item, {ID: 0})

# 	for item in data['Tools']:
# 		setattr(state, item, {ID: 0})
# 		check = 'made_{}'.format(item)
# 		setattr(state, check, {ID: False})

# 	for item, num in data['Initial'].items():
# 		setattr(state, item, {ID: num})

# 	return state

# def set_up_goals (data, ID):
# 	goals = []
# 	for item, num in data['Goal'].items():
# 		goals.append(('have_enough', ID, item, num))

# 	return goals

# if __name__ == '__main__':
# 	rules_filename = 'crafting.json'

# 	with open(rules_filename) as f:
# 		data = json.load(f)

# 	state = set_up_state(data, 'agent', 10) # allot time here
# 	goals = set_up_goals(data, 'agent')

# 	declare_operators(data)
# 	declare_methods(data)
# 	add_heuristic(data, 'agent')

# 	pyhop.print_operators()
# 	pyhop.print_methods()

# 	# Hint: verbose output can take a long time even if the solution is correct; 
# 	# try verbose=1 if it is taking too long
# 	pyhop.pyhop(state, goals, verbose=1)
# 	#pyhop.pyhop(state, [('have_enough', 'agent', 'plank', 1)], verbose=3)
    
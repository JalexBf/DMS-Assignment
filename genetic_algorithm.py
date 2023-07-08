import csv
import random
from deap import base, creator, tools

# Genetic Algorithm Parameters
POPULATION_SIZE = 100
NUM_GENERATIONS = 50
CROSSOVER_PROB = 0.8
MUTATION_PROB = 0.2
ELITE_SIZE = 10

# Desired range of disc desirability
MIN_DESIRE = 1
MAX_DESIRE = 5

# Load user money rates
user_money_rates = []
with open('user_money_rates.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        user_money_rates.append([float(val) for val in row])

# Load album prices
album_prices = []
with open('album_price.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        album_prices.append(float(row[0]))

# Create the fitness function
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

# Define the individual creation function
toolbox.register("individual", tools.initRepeat, creator.Individual, lambda: random.uniform(MIN_DESIRE, MAX_DESIRE),
                 n=len(album_prices))

# Define the population creation function
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


# Define the fitness function
def fitness(individual):
    if any(i >= len(user_money_rates[0]) - 1 for i in individual):
        return 0,
    individual = [int(i) for i in individual]
    total_cost = sum(album_prices[i] for i in individual)
    total_desire = sum(user_money_rates[j][i + 1] for j, i in enumerate(individual) if i < len(album_prices))
    fitness_score = max(0, total_desire - total_cost / 10.0)
    return fitness_score,


# Define crossover function
def crossover(parent1, parent2):
    crossover_point = random.randint(0, len(parent1) - 1)
    child = parent1[:crossover_point] + parent2[crossover_point:]
    return child,


# Define mutation function
def mutation(individual):
    index = random.randint(0, len(individual) - 1)
    album = random.randint(0, len(album_prices) - 1)
    individual[index] = album
    return individual,


def main():
    random.seed(42)

    # Create initial population
    population = toolbox.population(n=POPULATION_SIZE)

    # Register the fitness function
    toolbox.register("evaluate", fitness)

    # Register the crossover operator
    toolbox.register("mate", crossover)

    # Register the mutation operator
    toolbox.register("mutate", mutation)

    # Evaluate the entire population
    fitnesses = toolbox.map(toolbox.evaluate, population)
    for ind, fit in zip(population, fitnesses):
        ind.fitness.values = fit

    # Store the best individual of all generations
    best_individual = None

    for generation in range(NUM_GENERATIONS):
        # Select the next generation's parents
        parents = tools.selTournament(population, len(population) - ELITE_SIZE, tournsize=3)

        # Clone the selected parents
        offspring = [toolbox.clone(individual) for individual in parents]

        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CROSSOVER_PROB:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
            if random.random() < MUTATION_PROB:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        # Evaluate the individuals with invalid fitness values
        invalid_individuals = [individual for individual in offspring if not individual.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_individuals)
        for individual, fit in zip(invalid_individuals, fitnesses):
            individual.fitness.values = fit

        # Replace the old population with the offspring
        population[ELITE_SIZE:] = offspring

        # Update the best individual
        current_best = max(population, key=lambda x: x.fitness.values[0])
        if best_individual is None or current_best.fitness.values[0] > best_individual.fitness.values[0]:
            best_individual = toolbox.clone(current_best)

        # Print generation statistics
        print(
            f"Generation {generation + 1}: Best Desirability = {best_individual.fitness.values[0]}, Best Cost = {best_individual.fitness.values[0]}")

    print("Genetic Algorithm Results:")
    print(f"Best Desirability = {best_individual.fitness.values[0]}")

    # Compare with random selection
    random_selection = random.choices(population, k=1)[0]
    random_desirability = toolbox.evaluate(random_selection)[0]

    print("Random Selection Results:")
    print(f"Random Desirability = {random_desirability}")


if __name__ == "__main__":
    main()

'''
Stress test for the canvas
A simple genetic algorithm that reconstructs an image with rectangles
'''
from py5canvas import *
import numpy as np

population = []
population_size = 15
tournament_size = 5
num_rects = 200
num_parameters = 6
fitness = []
img = np.array(load_image('./images/frida128.png'))

def setup():
    print('setup')
    global population, fitness, img

    create_canvas(512, 512)
    # create initial population
    for i in range(population_size):
        dna = np.random.uniform(0, 1, num_rects*num_parameters)
        population.append(dna)
        fitness.append(0)
    fitness = np.array(fitness)


def draw():
    global population, fitness

    background(255)

    # evolve new generation
    population = evolve(population, fitness)

    # find fittest
    fittest = np.argmax(fitness)

    # draw the fittest result, but scale to the whole canvas sie
    background(255)
    push()
    scale_amt = width/img.shape[1]
    scale(scale_amt)
    # image(img, 0, 0)
    draw_phenotype(population[fittest])
    pop()

    # if the method is working this should be increasing
    fill(0)
    rect(0, 0, width, 30)
    fill(255)
    text_size(20)
    text("Generation %d, fitness: %.3f"%(frame_count+1, fitness[fittest]), 
         [20,20])


# tournament selection
# selects one chromosome with the best fitness among a set of random chromosomes
def tournament(population, fitness, size):
    n = len(fitness)
    I = np.random.choice(range(n), size=size, replace=True)
    T = fitness[I]
    return population[I[np.argmax(T)]]


def calc_phenotype(dna):
    num_rects = len(dna) // num_parameters
    rects = []
    j = 0
    for i in range(num_rects):
        rects.append( {
            'x': dna[j+0] * img.shape[1],
            'y': dna[j+1] * img.shape[0],
            'width': dna[j+2] * img.shape[1]*0.4,
            'height': dna[j+3] * img.shape[0]*0.4,
            'rotation': dna[j+4] * np.pi * 2,
            'opacity': dna[j+5]*255
            })
        j += num_parameters

    return rects


# draws an individual
def draw_phenotype(dna):
    phenotype = calc_phenotype(dna)
    for r in phenotype:
        no_stroke()
        fill(0, r['opacity']*0.5)
        push()
        translate(r['x'], r['y'])
        rotate(r['rotation'])
        rect(r['width']*0.5, r['height']*0.5, r['width'], r['height'])
        pop()


# computes fitness given a chromosome
def compute_fitness(dna):
    background(255)
    draw_phenotype(dna)
    # grab the resulting image
    canvas_img = get_image()[:img.shape[0],:img.shape[1]]
    cost = (canvas_img/255 - img/255)**2
    return -np.sum(cost)


# evolve a new generation
def evolve(population, fitness):
    n = len(population)
    # update fitness
    for i in range(n):
        fitness[i] = compute_fitness(population[i])

    # and create new generation
    generation = []
    for i in range(n):
        # parents
        a = tournament(population, fitness, tournament_size)
        b = tournament(population, fitness, tournament_size)
        # crossover
        dna = crossover(a, b)
        # muatate (modifies the dna in place)
        mutate(dna)
        # add new genotype to generation
        generation.append(dna)

    return generation


# crossover operator
def crossover(a, b):
    alpha = np.random.uniform(0, 1, len(a))
    return a*alpha + b*(1-alpha)


def mutate(dna, prob=0.001):
    n = len(dna)
    p = np.random.uniform(0, 1, n)
    mut = np.random.uniform(0, 1, n)
    I = np.where(p < prob)
    dna[I] = mut[I]

run()
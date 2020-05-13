import tensorflow as tf
import os.path
import Nets as nets
from numpy import asarray
from numpy import vstack
from numpy import arccos
from numpy import clip
from numpy import dot
from numpy import sin
from numpy import linspace
from numpy.linalg import norm
from matplotlib import pyplot as plt


def draw_2d_samples(generator, n_dim, seed=2019):
    noise = tf.random.normal([3000, n_dim], seed=seed)
    generated_image = generator(noise).numpy()
    return generated_image


def draw_samples(model, test_input):
    predictions = model(test_input, training=False)
    return predictions.numpy()


def write_config(args):
    file = open(os.path.join(args.dir, 'config.txt'), 'w')
    file.write(str(args))
    file.close()


def select_cogan_architecture(args):
    if args.g_arch == 'digit':
        generator1, generator2 = nets.cogan_generators_digit(args)
    elif args.g_arch == 'rotate':
        generator1, generator2 = nets.cogan_generators_rotate(args)
    elif args.g_arch == '256':
        generator1, generator2 = nets.cogan_generators_256(args)
    elif args.g_arch == 'face':
        generator1, generator2 = nets.cogan_generators_faces(args)
    elif args.g_arch == 'digit_noshare':
        generator1, generator2 = nets.cogan_generators_digit_noshare(args)

    if args.d_arch == 'digit':
        discriminator1, discriminator2 = nets.cogan_discriminators_digit(args)
    elif args.d_arch == 'rotate':
        discriminator1, discriminator2 = nets.cogan_discriminators_rotate(args)
    elif args.d_arch == '256':
        discriminator1, discriminator2 = nets.cogan_discriminators_256(args)
    elif args.d_arch == 'face':
        discriminator1, discriminator2 = nets.cogan_discriminators_faces(args)
    elif args.g_arch == 'digit_noshare':
        discriminator1, discriminator2 = nets.cogan_discriminators_digit_noshare(args)

    return generator1, generator2, discriminator1, discriminator2


def select_gan_architecture(args):
    if args.dataset == 'toy':
        generator = nets.toy_gen(args.noise_dim)
        discriminator = nets.toy_disc(args)
    elif args.gan_type == '64':
        generator = nets.gan64_gen(args)
        discriminator = nets.gan64_disc(args)
    elif args.gan_type == '128':
        generator = nets.gan128_gen(args)
        discriminator = nets.gan128_disc(args)
    elif args.gan_type == '256':
        generator = nets.gan256_gen(args)
        discriminator = nets.gan256_disc(args)
    elif args.gan_type == '32':
        generator = nets.cifargan_gen(args)
        discriminator = nets.cifargan_disc(args)
    else:
        raise NotImplementedError()

    return generator, discriminator


def select_weight_init(init_arg):
    if init_arg == 'normal':
        init = tf.keras.initializers.RandomNormal(0.02)
    elif init_arg == 'he':
        init = tf.keras.initializers.he_normal()
    elif init_arg == 'xavier':
        init = tf.keras.initializers.glorot_normal()
    else:
        raise NotImplementedError()
    return init


# spherical linear interpolation (slerp)
def slerp(val, low, high):
    omega = arccos(clip(dot(low/norm(low), high/norm(high)), -1, 1))
    so = sin(omega)
    if so == 0:
        # L'Hopital's rule/LERP
        return (1.0-val) * low + val * high
    return sin((1.0-val)*omega) / so * low + sin(val*omega) / so * high


# uniform interpolation between two points in latent space
def interpolate_points(p1, p2, steps):
    # interpolate ratios between the points
    ratios = linspace(0, 1, num=steps)
    # linear interpolate vectors
    vectors = list()
    for ratio in ratios:
        v = slerp(ratio, p1, p2)
        #v = (1.0 - ratio) * p1 + ratio * p2
        vectors.append(v)
    return asarray(vectors)


# create a plot of generated images
def plot_generated(examples, n, amount_of_pairs):
    # plot images
    for i in range(n * amount_of_pairs):
        # define subplot
        ax1=plt.subplot(amount_of_pairs, n, 1 + i)
        # turn off axis
        plt.axis('off')
        #plt.axis('on')
        #ax1.set_xticklabels([])
        #ax1.set_yticklabels([])
        # plot raw pixel data
        plt.imshow(examples[i, :, :, :])
    #plt.subplots_adjust(wspace=0, hspace=0)
    plt.show()


def latent_walk(gen1_dir, gen2_dir, z_dim=100, amount_of_pairs=1, steps=10):

    gen1 = tf.keras.models.load_model(gen1_dir)
    gen2 = tf.keras.models.load_model(gen2_dir)
    latent1 = tf.random.normal([amount_of_pairs*2, z_dim])

    res1 = None
    res2 = None
    for i in range(0, amount_of_pairs*2, 2):
        interpolated=interpolate_points(latent1[i], latent1[i+1], steps)
        X1 = gen1.predict(interpolated)
        X2 = gen2.predict(interpolated)
        X1 = 0.5 * X1 + 0.5
        X2 = 0.5 * X2 + 0.5
        if res1 is None:
            res1 = X1
            res2 = X2
        else:
            res1 = vstack((res1,X1))
            res2 = vstack((res2,X2))

    plot_generated(res1, steps, amount_of_pairs)
    plot_generated(res2, steps, amount_of_pairs)



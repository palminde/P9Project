import tensorflow as tf
import os.path
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
    for ele in vars(args):
        if str(ele) != 'seed':
            file.write(str(ele) + ': ' + str(vars(args)[ele]) + '\n')
    file.close()


def select_cogan_architecture(args):
    if args.g_arch == 'digit':
        generator1, generator2 = Nets.cogan_generators_digit(args)
    elif args.g_arch == 'rotate':
        generator1, generator2 = Nets.cogan_generators_rotate(args)
    elif args.g_arch == '256':
        generator1, generator2 = Nets.cogan_generators_256(args)
    elif args.g_arch == 'face':
        generator1, generator2 = Nets.cogan_generators_faces(args)
    elif args.g_arch == 'digit_noshare':
        generator1, generator2 = Nets.cogan_generators_digit_noshare(args)
    elif args.g_arch == 'face_noshare':
        generator1, generator2 = Nets.cogan_generators_faces_noshare(args)

    if args.d_arch == 'digit':
        discriminator1, discriminator2 = Nets.cogan_discriminators_digit(args)
    elif args.d_arch == 'rotate':
        discriminator1, discriminator2 = Nets.cogan_discriminators_rotate(args)
    elif args.d_arch == '256':
        discriminator1, discriminator2 = Nets.cogan_discriminators_256(args)
    elif args.d_arch == 'face':
        discriminator1, discriminator2 = Nets.cogan_discriminators_faces(args)
    elif args.g_arch == 'digit_noshare':
        discriminator1, discriminator2 = Nets.cogan_discriminators_digit_noshare(args)
    elif args.d_arch == 'face_noshare':
        discriminator1, discriminator2 = Nets.cogan_discriminators_faces_noshare(args)

    return generator1, generator2, discriminator1, discriminator2


def select_gan_architecture(args):
    if args.dataset == 'toy':
        generator = Nets.toy_gen(args.noise_dim)
        discriminator = Nets.toy_disc(args)
    elif args.gan_type == '64':
        generator = Nets.gan64_gen(args)
        discriminator = Nets.gan64_disc(args)
    elif args.gan_type == '128':
        generator = Nets.gan128_gen(args)
        discriminator = Nets.gan128_disc(args)
    elif args.gan_type == '256':
        generator = Nets.gan256_gen(args)
        discriminator = Nets.gan256_disc(args)
    elif args.gan_type == '32':
        generator = Nets.cifargan_gen(args)
        discriminator = Nets.cifargan_disc(args)
    else:
        raise NotImplementedError()

    return generator, discriminator


def select_weight_init(init_arg):
    if init_arg == 'normal':
        init = tf.keras.initializers.RandomNormal(stddev=0.02)
    elif init_arg == 'he':
        init = tf.keras.initializers.he_normal()
    elif init_arg == 'xavier':
        init = tf.keras.initializers.glorot_uniform()
    else:
        raise NotImplementedError()
    return init


def gen_noise(args, gen_sample_seed=False):
    if args.noise_type == 'normal':
        if gen_sample_seed:
            noise = tf.random.normal([args.num_samples_to_gen, args.noise_dim])
        else:
            noise = tf.random.normal([args.batch_size, args.noise_dim])
    elif args.noise_type == 'uniform':
        if gen_sample_seed:
            noise = tf.random.uniform(shape=(args.num_samples_to_gen, args.noise_dim), minval=-1, maxval=1)
        else:
            noise = tf.random.uniform(shape=(args.batch_size, args.noise_dim), minval=-1, maxval=1)
    else:
        raise NotImplementedError()
    return noise


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



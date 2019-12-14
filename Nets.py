import tensorflow as tf
from tensorflow import keras
layers = tf.keras.layers

#weight_init = tf.keras.initializers.RandomNormal(stddev=0.02)
weight_init = tf.keras.initializers.he_normal(seed=2019)

def tfgan_gen(args):
    g_dim = args.g_dim
    z_dim = args.noise_dim
    img_dim = args.img_dim
    channels = args.dataset_dim[3]

    model = keras.Sequential()
    model.add(layers.Dense(8 * 8 * g_dim, use_bias=False, kernel_initializer=weight_init, input_shape=(z_dim,)))
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU())
    model.add(layers.Reshape((8, 8, g_dim)))

    model.add(layers.Conv2DTranspose(int(g_dim/2), (5, 5), strides=(1, 1), kernel_initializer=weight_init, padding='same', use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU())

    model.add(layers.Conv2DTranspose(int(g_dim/4), (5, 5), strides=(2, 2), kernel_initializer=weight_init, padding='same', use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU())

    model.add(layers.Conv2DTranspose(channels, (5, 5), strides=(2, 2), padding='same', kernel_initializer=weight_init, use_bias=False, activation='tanh'))
    return model


def tfgan_disc(args):
    input_dim = args.img_dim
    d_dim = args.d_dim
    channels = args.dataset_dim[3]

    model = keras.Sequential()
    model.add(layers.Conv2D(d_dim, (3, 3), strides=(2, 2), kernel_initializer=weight_init, padding='same', input_shape=[input_dim, input_dim, channels]))
    model.add(layers.LeakyReLU())
    model.add(layers.Dropout(0.3))

    model.add(layers.Conv2D(d_dim*2, (3, 3), strides=(2, 2), kernel_initializer=weight_init, padding='same'))
    model.add(layers.LeakyReLU())
    model.add(layers.Dropout(0.3))

    model.add(layers.Flatten())
    model.add(layers.Dense(1, kernel_initializer=weight_init,))
    return model


def infogan_gen(args):
    zc_dim = args.zc_dim
    channels = args.dataset_dim[3]

    input = keras.Input(shape=(zc_dim,))
    # 8x8 feature maps
    n_nodes = 512 * 8 * 8
    g = layers.Dense(n_nodes, kernel_initializer=weight_init)(input)
    g = layers.Activation('relu')(g)
    g = layers.BatchNormalization()(g)
    g = layers.Reshape((8, 8, 512))(g)
    # normal
    g = layers.Conv2D(128, (4, 4), padding='same', kernel_initializer=weight_init)(g)
    g = layers.Activation('relu')(g)
    g = layers.BatchNormalization()(g)
    # upsample to 14g14
    g = layers.Conv2DTranspose(64, (4, 4), strides=(2, 2), padding='same', kernel_initializer=weight_init)(g)
    g = layers.Activation('relu')(g)
    g = layers.BatchNormalization()(g)
    # upsample to 28g28
    g = layers.Conv2DTranspose(channels, (4, 4), strides=(2, 2), padding='same', kernel_initializer=weight_init)(g)
    # tanh output
    output = layers.Activation('tanh')(g)
    # define model
    model = keras.Model(input, output)
    return model


def infogan_disc(args):
    input_dim = args.img_dim
    n_cat = args.n_cat

    # image input
    in_image = keras.Input(shape=input_dim)
    # downsample to 16x16
    d = layers.Conv2D(64, (4, 4), strides=(2, 2), padding='same', kernel_initializer=weight_init)(in_image)
    d = layers.LeakyReLU(alpha=0.1)(d)
    # downsample to 8x8
    d = layers.Conv2D(128, (4, 4), strides=(2, 2), padding='same', kernel_initializer=weight_init)(d)
    d = layers.LeakyReLU(alpha=0.1)(d)
    d = layers.BatchNormalization()(d)
    # normal
    d = layers.Conv2D(256, (4, 4), padding='same', kernel_initializer=weight_init)(d)
    d = layers.LeakyReLU(alpha=0.1)(d)
    d = layers.BatchNormalization()(d)
    # flatten feature maps
    d = layers.Flatten()(d)
    # real/fake output
    out_disc = layers.Dense(1, activation='sigmoid')(d)
    # define d model
    d_model = keras.Model(in_image, out_disc)

    # create q model layers
    q = layers.Dense(128)(d)
    q = layers.BatchNormalization()(q)
    q = layers.LeakyReLU(alpha=0.1)(q)
    # q model output - Currently only implemented for categorical codes and not continuous
    out_aux = layers.Dense(n_cat, activation='softmax')(q)
    # define q model
    q_model = keras.Model(in_image, out_aux)

    return d_model, q_model


# Presgan implementation of dcgan
conv_weight_init = tf.keras.initializers.RandomNormal(mean=0.0, stddev=0.02)
batchnorm_weight_init = tf.keras.initializers.RandomNormal(mean=0.0, stddev=0.02)
def presgan_gen(args):
    g_dim = args.g_dim
    z_dim = args.noise_dim
    img_dim = args.img_dim
    channels = args.dataset_dim[3]

    model = keras.Sequential()
    model.add(layers.Conv2DTranspose(g_dim*8, (4, 4), strides=(1, 1), padding='valid', kernel_initializer=conv_weight_init, use_bias=False, input_shape=(z_dim,)))
    model.add(layers.BatchNormalization())
    model.add(layers.ReLU())

    model.add(layers.Conv2DTranspose(g_dim*4, (4, 4), strides=(2, 2), padding='valid', kernel_initializer=conv_weight_init, use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.ReLU())

    model.add(layers.Conv2DTranspose(g_dim*2, (4, 4), strides=(2, 2), padding='valid', kernel_initializer=conv_weight_init, use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.ReLU())

    model.add(layers.Conv2DTranspose(g_dim, (4, 4), strides=(2, 2), padding='valid', kernel_initializer=conv_weight_init, use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.ReLU())

    model.add(layers.Conv2DTranspose(channels, (4, 4), strides=(2, 2), padding='valid', kernel_initializer=conv_weight_init, use_bias=False, activation='tanh'))
    return model


def presgan_disc(args):
    d_dim = args.d_dim
    input_dim = args.img_dim
    channels = args.dataset_dim[3]

    model = keras.Sequential()
    model.add(layers.Conv2D(d_dim, (4, 4), strides=(2, 2), padding='valid', kernel_initilizer=conv_weight_init, use_bias=False, input_shape=[input_dim, input_dim, channels]))
    model.add(layers.LeakyReLU(0.2))

    model.add(layers.Conv2D(d_dim*2, (4, 4), strides=(2, 2), padding='valid', kernel_initializer=conv_weight_init, use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU(0.2))

    model.add(layers.Conv2D(d_dim*4, (4, 4), strides=(2, 2), padding='valid', kernel_initializer=conv_weight_init, use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU(0.2))

    model.add(layers.Conv2D(d_dim*8, (4, 4), strides=(2, 2), padding='valid', kernel_initializer=conv_weight_init, use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU(0.2))

    model.add(layers.Conv2D(1, (4, 4), strides=(2, 2), padding='valid', kernel_initializer=conv_weight_init, use_bias=False, activation='sigmoid'))

    return model


# init norm dist, std=0.02, lrelu leak = 0.2, lr=0.0002, b1 = 0.5
def dcgan_gen(args):
    return 1


def dcgan_disc(args):
    return 1


def toy_gen(n_dim):
    inputs = keras.Input(shape=(n_dim,), name='digits')
    x = layers.Dense(128, activation='tanh', name='dense1')(inputs)
    x = layers.Dense(128, activation='tanh', name='dense2')(x)
    x = layers.Dense(128, activation='tanh', name='dense3')(x)
    outputs = layers.Dense(2, activation='tanh', name='preds')(x)
    model = keras.Model(inputs=inputs, outputs=outputs)
    return model


def toy_disc():
    inputs = keras.Input(shape=(256, 2), name='digits')
    x = layers.Dense(128, activation='tanh', name='dense1')(inputs)
    x = layers.Dense(128, activation='tanh', name='dense2')(x)
    x = layers.Dense(128, activation='tanh', name='dense3')(x)
    outputs = layers.Dense(1, name='preds')(x)
    model = keras.Model(inputs=inputs, outputs=outputs)
    return model


import tensorflow as tf

k_cross_entropy = tf.keras.losses.BinaryCrossentropy(from_logits=True)


def cross_entropy_gen(fake_output):
    G_loss = k_cross_entropy(tf.ones_like(fake_output), fake_output)
    return G_loss


def cross_entropy_disc(fake_output, real_output):
    true_labels = tf.ones_like(real_output)
    false_labels = tf.zeros_like(fake_output)
    #true_labels += 0.05 * tf.random.uniform(tf.shape(true_labels))
    #false_labels += 0.05 * tf.random.uniform(tf.shape(false_labels))
    real_loss = k_cross_entropy(true_labels, real_output)
    fake_loss = k_cross_entropy(false_labels, fake_output)
    D_loss = real_loss + fake_loss
    return D_loss


def wasserstein_gen(fake_output):
    G_loss = -tf.reduce_mean(fake_output)
    return G_loss


def wasserstein_disc(fake_output, real_output):
    D_loss = tf.reduce_mean(fake_output) - tf.reduce_mean(real_output)
    return D_loss


def set_losses(args):
    if args.loss == 'ce':
        return cross_entropy_disc, cross_entropy_gen
    elif args.loss == 'wgan':
        return wasserstein_disc, wasserstein_gen

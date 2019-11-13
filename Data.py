import tensorflow as tf
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def plot_distribution(samples, title='', cmap='Blues',x="x",y="y"):

    df = pd.DataFrame(samples, columns=["x", "y"])
    sns.jointplot(x="x", y="y", data=df, kind="kde")
    plt.show()

    ''' # From 'Are all GANS created equal':
    samples = samples.cpu().numpy()
    sns.set(font_scale=2)
    f, ax = plt.subplots(figsize=(4, 4))
    sns.kdeplot(samples[:, 0], samples[:, 1], cmap=cmap, ax=ax, n_levels=20, shade=True)
    plt.xlim([-5, 5])
    plt.ylim([-5, 5])
    plt.axis('off')
    plt.title(title)
    plt.show()'''


def draw_samples_and_plot_2d(generator, epoch):
    a = []
    for c in range(2000):
        noise = tf.random.normal([1, 10])
        generated_image = generator(noise, training=False)
        a.append(generated_image)

    samples = tf.convert_to_tensor(tf.reshape(a,[2000,2]))

    df = pd.DataFrame(samples, columns=["x", "y"])
    sns.jointplot(x="x", y="y", data=df, kind="kde")
    plt.savefig('image_at_epoch_{:04d}.png'.format(epoch))
    #plt.show()


def createToyDataRing(n_mixtures=8, radius=3, Ntrain=50176, std=0.05):
    delta_theta = 2 * np.pi / n_mixtures
    centers_x = []
    centers_y = []
    for i in range(n_mixtures):
        centers_x.append(radius * np.cos(i * delta_theta))
        centers_y.append(radius * np.sin(i * delta_theta))

    centers_x = np.expand_dims(np.array(centers_x), 1)
    centers_y = np.expand_dims(np.array(centers_y), 1)
    centers = np.concatenate([centers_x, centers_y], 1)

    p = [1. / n_mixtures for _ in range(n_mixtures)]

    ith_center = np.random.choice(n_mixtures, Ntrain, p=p)
    sample_centers = centers[ith_center, :]

    sample_points = np.random.normal(loc=sample_centers, scale=std).astype('float32')
    dat = tf.convert_to_tensor(sample_points)
    return dat
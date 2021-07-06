from PIL import Image
import matplotlib.pyplot as plt


def plot_image(filepath, **kwargs):
    plt.ion()
    img = np.array(Image.open(filepath))
    plt.imshow(img, **kwargs)


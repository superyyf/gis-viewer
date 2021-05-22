from PIL import Image

from src.ocr.paddleocr import PaddleOCR


def detectText(img_path):
    img_path = 'D:\project\gis-viewer\data\lp.png'
    ocr = PaddleOCR(use_angle_cls=True, use_gpu=False,
                    lang="ch")  # need to run only once to download and load model into memory
    result = ocr.ocr(img_path, cls=True)

    # image = Image.open(img_path).convert('RGB')
    # boxes = [line[0] for line in result]
    txts = [line[1][0] for line in result]
    # scores = [line[1][1] for line in result]
    # im_show = draw_ocr(image, boxes, txts, scores, font_path='D:\project\RS_UAV_Matching\src\ocr\doc\\fonts\simfang.ttf')
    # im_show = Image.fromarray(im_show)
    print(txts)
    return txts


def textParser(str_text):
    str1 = ''
    if len(str_text) != 0:
        for line in str_text:
            for ch in line:
                if ch.isdigit() or ch == 'N' or ch == 'E':
                    str1 += ch

    N_num = str1.index('N')
    E_num = str1.index('E')

    numE = [0, 0, 0]
    numE[0] = float(str1[E_num + 1:E_num + 4])
    numE[1] = float(str1[E_num + 4:E_num + 6]) / 60
    numE[2] = float(str1[E_num + 6:N_num]) / 3600

    numN = [0, 0, 0]
    numN[0] = float(str1[N_num + 1:N_num + 4])
    numN[1] = float(str1[N_num + 4:N_num + 6]) / 60
    numN[2] = float(str1[N_num + 6:]) / 3600

    e = round(sum(numE), 4)
    n = round(sum(numN), 4)

    return [e, n]


if __name__ == '__main__':
    img_path = 'D:\project\RS_UAV_Matching\src\ocr\doc\imgs\\11.jpg'
    detectText(img_path)

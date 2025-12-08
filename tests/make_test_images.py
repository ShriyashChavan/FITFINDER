from PIL import Image, ImageDraw

img1 = Image.new('RGB',(400,600),(200,180,220))
d1 = ImageDraw.Draw(img1)
d1.text((20,20),'Person',(10,10,10))
img1.save('tests/test_person.jpg')

img2 = Image.new('RGBA',(300,300),(255,200,200,255))
d2 = ImageDraw.Draw(img2)
d2.rectangle((50,50,250,250),(100,50,150))
img2.save('tests/test_cloth.png')

print('Created tests/test_person.jpg and tests/test_cloth.png')

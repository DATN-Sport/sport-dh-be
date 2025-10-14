
class MappingData:
    def __init__(self, obj_images = None, obj_centers = None, obj_fields = None):
        self.obj_images = obj_images
        self.obj_centers = obj_centers
        self.obj_fields = obj_fields

    def mapping_img(self):
        image_map = {}
        for img in self.obj_images:
            image_info = {
                'id': img['id'],
                'preview': img['preview'],
                'file': img['file']
            }
            image_map.setdefault(img['object_id'], []).append(image_info)
        return image_map


    # def mapping_centers(self):
    #     center_map = {}
    #     for center in self.obj_centers:
    #         ce
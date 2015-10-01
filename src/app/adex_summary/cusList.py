__author__ = 'hao'


def del_list_by_indices(old_list, indices):
    indices_set = set(indices)
    new_list = [item for index, item in enumerate(old_list) if index not in indices_set]
    return new_list

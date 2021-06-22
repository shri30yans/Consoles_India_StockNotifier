count_dict={   "PS5":{"amazon":0,"flipkart":0,"games_the_shop":0,"ppgc":0},
                "XSX":{"amazon":0,"flipkart":0},
                "XSS":{"amazon":0,"flipkart":0}}
def add_count(website_name,product):
    try:
        print(count_dict[product][website_name])
        count_dict[product][website_name]+=1
    except:
        print("Add count exception")
print(count_dict)
add_count("amazon","PS5")
print(count_dict)
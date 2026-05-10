---
name: add-to-cart-links
description: >-
  Builds Amazon.in bulk add-to-cart URLs with Associates tracking (tag / ASIN.n /
  Quantity.n). Use when the user wants add-to-cart links, ATC URLs, Amazon cart
  links, or multi-item Amazon.in checkout shortcuts.
---

# Amazon.in add-to-cart (ATC) links

## One product

```
https://www.amazon.in/gp/aws/cart/add.html?tag=YOUR_TRACKING_ID&ASIN.1=B0XXXXXXXX&Quantity.1=1
```

- **`YOUR_TRACKING_ID`** — Associates store / tracking ID for **Amazon.in** (same value as `tag=` on normal affiliate links).
- **`ASIN.1`** — product ASIN from the URL `amazon.in/dp/B0XXXXXXXX/`.
- **`Quantity.1`** — quantity for that ASIN.

## Several products in one link

Use numbered pairs `ASIN.n` and `Quantity.n` for each line:

```
https://www.amazon.in/gp/aws/cart/add.html?tag=YOUR_TRACKING_ID&ASIN.1=B0AAA&Quantity.1=1&ASIN.2=B0BBB&Quantity.2=1&ASIN.3=B0CCC&Quantity.3=1
```

## Finding ASINs

- Open the product page and copy from `/dp/ASIN/`.
- Or take ASINs from wishlist HTML/links that contain `/dp/ASIN/`.

## Note

Some examples use `AssociateTag=` instead of `tag=`. If attribution fails in testing, try the other parameter with the **same** tracking ID. Follow Associates disclosure and link policies.

## See also

- **`high-value-india-deal-posts`** — deal-focused social copy (same-SKU pricing, effective ₹, disclosure) when promoting product URLs rather than cart shortcuts.

